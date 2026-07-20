from __future__ import annotations

import subprocess
from pathlib import Path
import time

from foreman_ai_hq import db
from foreman_ai_hq.project_context import project_task_metadata
from foreman_ai_hq.task_launch import TaskLaunchBlocked, detect_pr_capability, launch_task


def _wait_for_worker_run(db_path: Path, task_id: str, status: str | None = None):
    deadline = time.time() + 5
    while time.time() < deadline:
        runs = db.list_worker_runs(db_path, task_id=task_id)
        if runs and (status is None or runs[-1]["status"] == status):
            return runs[-1]
        time.sleep(0.01)
    raise AssertionError("worker run did not reach expected status")


def _git_project(tmp_path: Path, *, test_command: str | None = "python -m pytest") -> Path:
    root = tmp_path / "write-project"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname = 'write-demo'\n")
    (root / "test_sample.py").write_text("def test_ok():\n    assert True\n")
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=demo@example.com", "-c", "user.name=Demo", "commit", "-m", "initial"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    if test_command is None:
        (root / "pyproject.toml").unlink()
        subprocess.run(["git", "rm", "pyproject.toml"], cwd=root, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.email=demo@example.com", "-c", "user.name=Demo", "commit", "-m", "remove test marker"],
            cwd=root,
            check=True,
            capture_output=True,
        )
    return root


def _verified_task(db_path: Path, root: Path, *, test_command: str | None = "python -m pytest"):
    db.init_db(db_path)
    project = db.upsert_connected_project(
        db_path,
        name="Write Project",
        root_path=str(root),
        profile={"test_command": test_command, "root_path": str(root)},
        capability={"state": "launch_ready", "can_launch": True},
    )
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(root),
        config={"launch_template": ["python", "-c", "print('worker')"]},
        supported_models=["opencode/gpt-5.1"],
        is_default=True,
    )
    db.mark_worker_adapter_verification(db_path, "opencode", verified=True, evidence={"ok": True})
    return db.create_task(
        db_path,
        description="Write code change",
        status="Ready",
        estimate_tokens=1000,
        recommended_model="opencode/gpt-5.1",
        metadata={
            **project_task_metadata(project),
            "launch_mode": "write_capable",
        },
    )


def _record_worker_usage(db_path: Path, plan):
    db.record_token_turn(
        db_path,
        session_id=plan.metadata["session_id"],
        usage_kind="task_execution",
        model="opencode/gpt-5.1",
        prompt_tokens=10,
        completion_tokens=5,
        cost=0,
        raw_usage={"total_tokens": 15},
    )


def test_write_capable_launch_blocks_dirty_repo_before_runner(tmp_path):
    db_path = tmp_path / "harness.db"
    root = _git_project(tmp_path)
    (root / "dirty.py").write_text("print('dirty')\n")
    task = _verified_task(db_path, root)
    calls = []

    try:
        launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=calls.append)
    except TaskLaunchBlocked as exc:
        blocked = exc.task
    else:
        raise AssertionError("expected dirty repo to block")

    assert blocked["status"] == "Blocked"
    assert "clean working tree" in blocked["metadata"]["launch_blocked_reason"]
    assert calls == []


def test_write_capable_codex_native_launch_blocks_non_git_project_before_runner(tmp_path):
    db_path = tmp_path / "harness.db"
    root = tmp_path / "non-git-project"
    root.mkdir()
    db.init_db(db_path)
    project = db.upsert_connected_project(
        db_path,
        name="Non Git Project",
        root_path=str(root),
        profile={"root_path": str(root)},
        capability={"state": "launch_ready", "can_launch": True},
    )
    db.update_worker_adapter(
        db_path,
        "codex",
        workdir=str(root),
        config={"command": "codex"},
        supported_models=["gpt-5.6-terra"],
        is_default=True,
    )
    db.mark_worker_adapter_verification(
        db_path,
        "codex",
        verified=True,
        evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
    )
    task = db.create_task(
        db_path,
        description="Write Codex change",
        status="Ready",
        estimate_tokens=1000,
        recommended_model="gpt-5.6-terra",
        metadata={**project_task_metadata(project), "launch_mode": "write_capable"},
    )
    calls = []

    def runner(plan):
        calls.append(plan)
        return {"returncode": 0, "stdout": "", "stderr": ""}

    try:
        launch_task(db_path, task["id"], adapter_id="codex", model=None, proxy_url=None, runner=runner)
    except TaskLaunchBlocked as exc:
        blocked = exc.task
    else:
        raise AssertionError("expected non-git project to block")

    assert blocked["status"] == "Blocked"
    assert "git repository" in blocked["metadata"]["launch_blocked_reason"]
    assert calls == []


def test_write_capable_launch_creates_task_branch_runs_tests_and_commits(tmp_path):
    db_path = tmp_path / "harness.db"
    root = _git_project(tmp_path)
    task = _verified_task(db_path, root, test_command="python -m pytest")

    def runner(plan):
        _record_worker_usage(db_path, plan)
        (root / "feature.py").write_text("VALUE_2099 = 'DEMO'\n")
        return {"returncode": 0, "stdout": "changed", "stderr": ""}

    result = launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=runner)
    assert result.task["status"] == "Running"
    _wait_for_worker_run(db_path, task["id"], "completed")
    launched = db.get_task(db_path, task["id"])
    metadata = launched["metadata"]
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    commit_message = subprocess.run(["git", "log", "-1", "--pretty=%B"], cwd=root, check=True, capture_output=True, text=True).stdout
    porcelain = subprocess.run(["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()

    assert launched["status"] == "Review"
    assert metadata["launch_mode"] == "write_capable"
    assert metadata["task_branch"] == branch
    assert branch.startswith("foremanctl/task-")
    assert metadata["post_run_verification"]["passed"] is True
    assert metadata["diff_summary"]["files_changed"] == ["feature.py"]
    assert metadata["harness_commit"]["sha"]
    assert task["id"] in commit_message
    assert porcelain == ""


def test_write_capable_verification_uses_current_connected_project_profile(tmp_path):
    db_path = tmp_path / "harness.db"
    root = _git_project(tmp_path)
    task = _verified_task(db_path, root, test_command="python -m pytest")
    db.update_task(
        db_path,
        task["id"],
        {
            "metadata": {
                **task["metadata"],
                "project_profile": {
                    **task["metadata"]["project_profile"],
                    "test_command": "python -c 'raise SystemExit(1)'",
                },
            }
        },
    )

    def runner(plan):
        _record_worker_usage(db_path, plan)
        (root / "feature.py").write_text("VALUE_2099 = 'DEMO'\n")
        return {"returncode": 0, "stdout": "changed", "stderr": ""}

    launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=runner)
    _wait_for_worker_run(db_path, task["id"], "completed")
    launched = db.get_task(db_path, task["id"])

    assert launched["status"] == "Review"
    assert launched["metadata"]["post_run_verification"]["passed"] is True
    assert launched["metadata"]["post_run_verification"]["command"] == "python -m pytest"


def test_write_capable_missing_test_command_requires_manual_approval_before_commit(tmp_path):
    db_path = tmp_path / "harness.db"
    root = _git_project(tmp_path, test_command=None)
    task = _verified_task(db_path, root, test_command=None)

    def runner(plan):
        _record_worker_usage(db_path, plan)
        (root / "manual.txt").write_text("DEMO manual review\n")
        return {"returncode": 0, "stdout": "changed", "stderr": ""}

    result = launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=runner)
    assert result.task["status"] == "Running"
    _wait_for_worker_run(db_path, task["id"], "completed")
    completed = db.get_task(db_path, task["id"])
    metadata = completed["metadata"]
    porcelain = subprocess.run(["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True).stdout

    assert completed["status"] == "Review"
    assert metadata["manual_commit_approval_required"] is True
    assert metadata["post_run_verification"]["reason"] == "No test command configured."
    assert "harness_commit" not in metadata
    assert "manual.txt" in porcelain


def test_write_capable_verification_failure_preserves_uncommitted_diff(tmp_path):
    db_path = tmp_path / "harness.db"
    root = _git_project(tmp_path, test_command="python -m pytest")
    task = _verified_task(db_path, root, test_command="python -m pytest")

    def runner(plan):
        _record_worker_usage(db_path, plan)
        (root / "test_sample.py").write_text("def test_bad():\n    assert False\n")
        return {"returncode": 0, "stdout": "changed", "stderr": ""}

    launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=runner)
    _wait_for_worker_run(db_path, task["id"], "failed")
    blocked = db.get_task(db_path, task["id"])

    metadata = blocked["metadata"]
    porcelain = subprocess.run(["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True).stdout
    assert blocked["status"] == "Blocked"
    assert metadata["post_run_verification"]["passed"] is False
    assert "test_sample.py" in metadata["diff_summary"]["stat"]
    assert "test_sample.py" in porcelain


def test_write_capable_no_diff_blocks_instead_of_review(tmp_path):
    db_path = tmp_path / "harness.db"
    root = _git_project(tmp_path, test_command="python -m pytest")
    task = _verified_task(db_path, root, test_command="python -m pytest")

    def runner(plan):
        _record_worker_usage(db_path, plan)
        return {"returncode": 0, "stdout": "no changes", "stderr": ""}

    launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=runner)
    run = _wait_for_worker_run(db_path, task["id"], "failed")
    blocked = db.get_task(db_path, task["id"])

    assert blocked["status"] == "Blocked"
    assert blocked["actual_tokens"] == 15
    assert blocked["metadata"]["launch_blocked_reason"] == "Worker completed but produced no code changes."
    assert blocked["metadata"]["diff_summary"]["has_changes"] is False
    assert run["error_message"] == "Worker completed but produced no code changes."


def test_pr_capability_detection_handles_missing_github_remote(tmp_path):
    root = _git_project(tmp_path)

    capability = detect_pr_capability(root)

    assert capability["available"] is False
    assert capability["github_remote"] is False
    assert "GitHub remote" in capability["reason"]
