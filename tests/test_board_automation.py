from pathlib import Path

from agile_ai_htb import db
from agile_ai_htb.board_automation import (
    QUEUE_STATUS_RUNNING,
    QUEUE_STATUS_STOPPED,
    RUN_QUEUE_SOURCE,
    RUN_NEXT_SOURCE,
    get_run_automation_state,
    list_eligible_estimated_tasks,
    record_automation_event,
    start_run_automation,
    stop_run_automation,
)
from agile_ai_htb.project_context import project_task_metadata


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    return db_path


def _project(db_path: Path, root: Path, name: str) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    return db.upsert_connected_project(
        db_path,
        name=name,
        root_path=str(root.resolve()),
        profile={"name": name, "root_path": str(root.resolve()), "test_command": "pytest"},
        capability={"state": "launch_ready", "can_launch": True},
    )


def _estimated_task(db_path: Path, project: dict, description: str) -> dict:
    return db.create_task(
        db_path,
        description=description,
        status="Estimated",
        estimate_tokens=1000,
        recommended_model="opencode/gpt-5.1",
        metadata=project_task_metadata(project),
    )


def test_run_automation_state_is_persisted_with_policy(tmp_path):
    db_path = _init_db(tmp_path)
    project = _project(db_path, tmp_path / "repo", "repo")

    state = start_run_automation(
        db_path,
        project_id=project["id"],
        source=RUN_QUEUE_SOURCE,
        auto_agent_review=True,
        active_task_id="task_123",
        active_worker_run_id="run_123",
    )

    assert state["status"] == QUEUE_STATUS_RUNNING
    assert state["project_id"] == project["id"]
    assert state["source"] == RUN_QUEUE_SOURCE
    assert state["active_task_id"] == "task_123"
    assert state["active_worker_run_id"] == "run_123"
    assert state["auto_agent_review"] is True
    assert state["policy"]["concurrency"] == 1
    assert state["policy"]["human_disposition_required"] is True

    loaded = get_run_automation_state(db_path, project["id"])
    assert loaded["status"] == QUEUE_STATUS_RUNNING
    assert loaded["policy"]["auto_agent_review"] is True


def test_eligible_estimated_tasks_are_project_scoped_and_deterministic(tmp_path):
    db_path = _init_db(tmp_path)
    project_a = _project(db_path, tmp_path / "repo-a", "repo-a")
    project_b = _project(db_path, tmp_path / "repo-b", "repo-b")
    first = _estimated_task(db_path, project_a, "first")
    second = _estimated_task(db_path, project_a, "second")
    _estimated_task(db_path, project_b, "other project")
    db.create_task(db_path, description="unbound", status="Estimated", estimate_tokens=100)
    db.create_task(
        db_path,
        description="review task",
        status="Review",
        metadata=project_task_metadata(project_a),
    )

    eligible = list_eligible_estimated_tasks(db_path, project_a["id"])

    assert [task["id"] for task in eligible] == [first["id"], second["id"]]
    assert all(task["metadata"]["connected_project_id"] == project_a["id"] for task in eligible)


def test_queue_stop_reason_and_automation_events_are_recorded(tmp_path):
    db_path = _init_db(tmp_path)
    project = _project(db_path, tmp_path / "repo", "repo")
    task = _estimated_task(db_path, project, "queued task")
    session = db.create_session(
        db_path,
        task_description=task["description"],
        model="opencode/gpt-5.1",
        session_key_hash="hash",
        guardrail_overrides={},
    )
    run = db.create_worker_run(
        db_path,
        task_id=task["id"],
        session_id=session["id"],
        adapter_id="opencode",
        model="opencode/gpt-5.1",
        tracking_mode="proxy_governed",
        command_plan={"command": ["opencode", "run"]},
        metadata={"existing": True},
    )

    stop_run_automation(
        db_path,
        project_id=project["id"],
        reason="retryable_failure",
        detail={"retryable": True},
        task_id=task["id"],
        worker_run_id=run["id"],
    )

    state = get_run_automation_state(db_path, project["id"])
    assert state["status"] == QUEUE_STATUS_STOPPED
    assert state["latest_stop_reason"] == "retryable_failure"
    assert state["events"][-1]["kind"] == "automation_stopped"

    updated_task = db.get_task(db_path, task["id"])
    assert updated_task["metadata"]["automation_events"][-1]["detail"]["retryable"] is True

    updated_run = db.get_worker_run(db_path, run["id"])
    assert updated_run["metadata"]["existing"] is True
    assert updated_run["metadata"]["automation"]["kind"] == "automation_stopped"

    events = db.list_worker_run_events(db_path, worker_run_id=run["id"])
    assert events[-1]["kind"] == "automation_stopped"
    assert events[-1]["detail"]["reason"] == "retryable_failure"


def test_task_automation_event_does_not_change_task_status(tmp_path):
    db_path = _init_db(tmp_path)
    project = _project(db_path, tmp_path / "repo", "repo")
    task = _estimated_task(db_path, project, "event task")

    record_automation_event(
        db_path,
        project_id=project["id"],
        kind="automation_skipped",
        title="Task skipped",
        detail={"reason": "no_allowed_model"},
        task_id=task["id"],
    )

    updated = db.get_task(db_path, task["id"])
    assert updated["status"] == "Estimated"
    assert updated["metadata"]["automation_events"][-1]["detail"]["reason"] == "no_allowed_model"


def test_invalid_automation_source_is_rejected(tmp_path):
    db_path = _init_db(tmp_path)
    project = _project(db_path, tmp_path / "repo", "repo")

    try:
        start_run_automation(db_path, project_id=project["id"], source="autopilot")
    except ValueError as exc:
        assert "unsupported automation source" in str(exc)
    else:
        raise AssertionError("invalid automation source was accepted")

    start_run_automation(db_path, project_id=project["id"], source=RUN_NEXT_SOURCE)
    assert get_run_automation_state(db_path, project["id"])["source"] == RUN_NEXT_SOURCE
