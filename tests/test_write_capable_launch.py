from __future__ import annotations

import subprocess
from pathlib import Path

from agile_ai_htb import db
from agile_ai_htb.task_launch import TaskLaunchBlocked, detect_pr_capability, launch_task


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
            "launch_mode": "write_capable",
            "connected_project_id": "proj_demo_2099",
            "project_root_path": str(root),
            "project_profile": {"test_command": test_command, "root_path": str(root)},
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


def test_write_capable_launch_creates_task_branch_runs_tests_and_commits(tmp_path):
    db_path = tmp_path / "harness.db"
    root = _git_project(tmp_path)
    task = _verified_task(db_path, root, test_command="python -m pytest")

    def runner(plan):
        _record_worker_usage(db_path, plan)
        (root / "feature.py").write_text("VALUE_2099 = 'DEMO'\n")
        return {"returncode": 0, "stdout": "changed", "stderr": ""}

    result = launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=runner)
    launched = result.task
    metadata = launched["metadata"]
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    commit_message = subprocess.run(["git", "log", "-1", "--pretty=%B"], cwd=root, check=True, capture_output=True, text=True).stdout
    porcelain = subprocess.run(["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()

    assert launched["status"] == "Review"
    assert metadata["launch_mode"] == "write_capable"
    assert metadata["task_branch"] == branch
    assert branch.startswith("htb/task-")
    assert metadata["post_run_verification"]["passed"] is True
    assert metadata["diff_summary"]["files_changed"] == ["feature.py"]
    assert metadata["harness_commit"]["sha"]
    assert task["id"] in commit_message
    assert porcelain == ""


def test_write_capable_missing_test_command_requires_manual_approval_before_commit(tmp_path):
    db_path = tmp_path / "harness.db"
    root = _git_project(tmp_path, test_command=None)
    task = _verified_task(db_path, root, test_command=None)

    def runner(plan):
        _record_worker_usage(db_path, plan)
        (root / "manual.txt").write_text("DEMO manual review\n")
        return {"returncode": 0, "stdout": "changed", "stderr": ""}

    result = launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=runner)
    metadata = result.task["metadata"]
    porcelain = subprocess.run(["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True).stdout

    assert result.task["status"] == "Review"
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

    try:
        launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=runner)
    except TaskLaunchBlocked as exc:
        blocked = exc.task
    else:
        raise AssertionError("expected verification failure to block")

    metadata = blocked["metadata"]
    porcelain = subprocess.run(["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True).stdout
    assert blocked["status"] == "Blocked"
    assert metadata["post_run_verification"]["passed"] is False
    assert "test_sample.py" in metadata["diff_summary"]["stat"]
    assert "test_sample.py" in porcelain


def test_pr_capability_detection_handles_missing_github_remote(tmp_path):
    root = _git_project(tmp_path)

    capability = detect_pr_capability(root)

    assert capability["available"] is False
    assert capability["github_remote"] is False
    assert "GitHub remote" in capability["reason"]
