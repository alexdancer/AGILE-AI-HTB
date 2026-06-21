from pathlib import Path
import time

from agile_ai_htb import db
from agile_ai_htb.execution_backend import LocalExecutionBackend, detect_project_profile, validate_local_project_path
from agile_ai_htb.task_launch import TaskLaunchBlocked, launch_task


def _wait_for_worker_run(db_path: Path, task_id: str, status: str | None = None):
    deadline = time.time() + 2
    while time.time() < deadline:
        runs = db.list_worker_runs(db_path, task_id=task_id)
        if runs and (status is None or runs[-1]["status"] == status):
            return runs[-1]
        time.sleep(0.01)
    raise AssertionError("worker run did not reach expected status")


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "demo-project"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname = "demo"\ndependencies = ["fastapi"]\n')
    (root / "README.md").write_text("# Demo\n")
    (root / "src").mkdir()
    return root


def test_local_project_validation_rejects_missing_and_non_project_paths(tmp_path):
    assert validate_local_project_path(tmp_path / "missing") == "Local project path does not exist."

    empty = tmp_path / "empty"
    empty.mkdir()
    error = validate_local_project_path(empty)
    assert error is not None
    assert "project markers" in error


def test_profile_detection_records_lightweight_project_context(tmp_path):
    root = _project_root(tmp_path)

    profile = detect_project_profile(root)

    assert profile["name"] == "demo-project"
    assert profile["root_path"] == str(root.resolve())
    assert profile["language_hints"] == ["python"]
    assert "fastapi" in profile["framework_hints"]
    assert "pip" in profile["package_manager_hints"]
    assert profile["test_command"] == "pytest"
    assert "src" in profile["top_level_folders"]
    assert "README.md" in profile["relevant_docs"]


def test_local_execution_backend_persists_project_profile_and_analysis_capability(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    root = _project_root(tmp_path)

    result = LocalExecutionBackend(db_path).connect_project(root)

    assert result.error is None
    assert result.project is not None
    project = db.list_connected_projects(db_path)[0]
    assert project["root_path"] == str(root.resolve())
    assert project["profile"]["test_command"] == "pytest"
    assert project["capability"]["state"] == "analysis_ready"
    assert "No verified launchable Worker Adapter is available." in project["capability"]["reasons"]
    backend_status = db.get_execution_backend_status(db_path, "local_runner")
    assert backend_status["online"] is True


def test_project_capability_stays_analysis_ready_with_observed_only_adapter(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    root = _project_root(tmp_path)
    db.mark_worker_adapter_verification(
        db_path,
        "opencode",
        verified=True,
        evidence={"tracking_mode": "observed_only", "tracking_authoritative": False},
    )

    result = LocalExecutionBackend(db_path).connect_project(root)

    assert result.project is not None
    assert result.project["capability"]["state"] == "analysis_ready"
    assert "No verified launchable Worker Adapter is available." in result.project["capability"]["reasons"]


def test_project_capability_is_launch_ready_with_online_backend_and_verified_adapter(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    root = _project_root(tmp_path)
    db.mark_worker_adapter_verification(db_path, "opencode", verified=True, evidence={"ok": True})

    result = LocalExecutionBackend(db_path).connect_project(root)

    assert result.project is not None
    assert result.project["capability"]["state"] == "launch_ready"
    assert result.project["capability"]["label"] == "Launch-ready via Local Runner"
    assert result.project["capability"]["reasons"] == []



def test_read_only_proof_task_launches_in_connected_repo_and_persists_report(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    root = _project_root(tmp_path)
    db.mark_worker_adapter_verification(db_path, "opencode", verified=True, evidence={"ok": True})
    backend = LocalExecutionBackend(db_path)
    project = backend.connect_project(root).project
    assert project is not None
    task = backend.create_read_only_proof_task(project)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
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
        return {"returncode": 0, "stdout": "report complete", "stderr": ""}

    result = launch_task(
        db_path,
        task["id"],
        adapter_id="opencode",
        model="opencode/gpt-5.1",
        proxy_url="http://127.0.0.1:8000/v1",
        runner=fake_runner,
    )

    assert result.task["status"] == "Running"
    _wait_for_worker_run(db_path, task["id"], "completed")
    assert runner_calls[0].cwd == root.resolve()
    assert runner_calls[0].env["OPENAI_BASE_URL"] == "http://127.0.0.1:8000/v1"
    refreshed = db.get_task(db_path, task["id"])
    refreshed = db.get_task(db_path, task["id"])
    assert refreshed["status"] == "Review"
    assert refreshed["metadata"]["session_report"]["test_command"] == "pytest"
    assert "src" in refreshed["metadata"]["session_report"]["top_level_structure"]


def test_read_only_proof_blocks_when_no_worker_model_call_observed(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    root = _project_root(tmp_path)
    db.mark_worker_adapter_verification(db_path, "opencode", verified=True, evidence={"ok": True})
    backend = LocalExecutionBackend(db_path)
    project = backend.connect_project(root).project
    assert project is not None
    task = backend.create_read_only_proof_task(project)

    launch_task(
        db_path,
        task["id"],
        adapter_id="opencode",
        model="opencode/gpt-5.1",
        proxy_url="http://127.0.0.1:8000/v1",
        runner=lambda plan: {"returncode": 0, "stdout": "no model call", "stderr": ""},
    )
    _wait_for_worker_run(db_path, task["id"], "failed")
    blocked = db.get_task(db_path, task["id"])

    assert blocked["status"] == "Estimated"
    assert blocked["metadata"]["launch_error"] == "No Worker model call was observed through the Harness Proxy."
    assert blocked["metadata"]["launch_failure_type"] == "missing_proxy_worker_usage"
    assert blocked["metadata"]["launch_retryable"] is True
    assert blocked["metadata"]["launch_guardrail_reasons"] == ["No Worker model call was observed through the Harness Proxy."]
    assert "launch_blocked_reason" not in blocked["metadata"]


def test_read_only_proof_blocks_when_worker_modifies_files(tmp_path):
    import subprocess

    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    root = _project_root(tmp_path)
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=demo@example.com", "-c", "user.name=Demo", "commit", "-m", "initial"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    db.mark_worker_adapter_verification(db_path, "opencode", verified=True, evidence={"ok": True})
    backend = LocalExecutionBackend(db_path)
    project = backend.connect_project(root).project
    assert project is not None
    task = backend.create_read_only_proof_task(project)

    def modifying_runner(plan):
        (root / "src" / "changed.py").write_text("print('changed')\n")
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
        return {"returncode": 0, "stdout": "modified", "stderr": ""}

    launch_task(
        db_path,
        task["id"],
        adapter_id="opencode",
        model="opencode/gpt-5.1",
        proxy_url="http://127.0.0.1:8000/v1",
        runner=modifying_runner,
    )
    _wait_for_worker_run(db_path, task["id"], "failed")
    blocked = db.get_task(db_path, task["id"])

    assert blocked["status"] == "Blocked"
    assert blocked["metadata"]["launch_blocked_reason"] == "Read-only Worker session modified the connected project."
    assert "src/" in blocked["metadata"]["readonly_diff_evidence"]["after"]
