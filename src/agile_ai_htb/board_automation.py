from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agile_ai_htb import db
from agile_ai_htb.project_context import task_matches_project

RUN_NEXT_SOURCE = "run_next"
RUN_QUEUE_SOURCE = "run_queue"
QUEUE_STATUS_IDLE = "idle"
QUEUE_STATUS_RUNNING = "running"
QUEUE_STATUS_STOPPED = "stopped"


DEFAULT_POLICY = {
    "scope": "project",
    "concurrency": 1,
    "eligible_statuses": ["Estimated"],
    "auto_agent_review": False,
    "stop_before_budget_override": True,
    "stop_before_native_usage_ack": True,
    "human_disposition_required": True,
}


def empty_run_automation_state(project_id: str) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "status": QUEUE_STATUS_IDLE,
        "source": None,
        "active_task_id": None,
        "active_worker_run_id": None,
        "auto_agent_review": False,
        "policy": dict(DEFAULT_POLICY),
        "latest_stop_reason": None,
        "events": [],
    }


def get_run_automation_state(database_path: Path | str, project_id: str) -> dict[str, Any]:
    state = db.get_portal_setting(database_path, _state_key(project_id), empty_run_automation_state(project_id))
    return _normalize_state(project_id, state)


def save_run_automation_state(database_path: Path | str, state: dict[str, Any]) -> dict[str, Any]:
    project_id = str(state["project_id"])
    normalized = _normalize_state(project_id, state)
    return db.set_portal_setting(database_path, _state_key(project_id), normalized)


def start_run_automation(
    database_path: Path | str,
    *,
    project_id: str,
    source: str,
    auto_agent_review: bool = False,
    active_task_id: str | None = None,
    active_worker_run_id: str | None = None,
) -> dict[str, Any]:
    if source not in {RUN_NEXT_SOURCE, RUN_QUEUE_SOURCE}:
        raise ValueError(f"unsupported automation source: {source}")
    def update(state: dict[str, Any]) -> dict[str, Any]:
        state = _normalize_state(project_id, state)
        policy = {**DEFAULT_POLICY, **dict(state.get("policy") or {})}
        policy["auto_agent_review"] = bool(auto_agent_review)
        state.update(
            {
                "status": QUEUE_STATUS_RUNNING,
                "source": source,
                "active_task_id": active_task_id,
                "active_worker_run_id": active_worker_run_id,
                "auto_agent_review": bool(auto_agent_review),
                "policy": policy,
                "latest_stop_reason": None,
            }
        )
        return state

    db.update_portal_setting(database_path, _state_key(project_id), empty_run_automation_state(project_id), update)
    return record_automation_event(
        database_path,
        project_id=project_id,
        kind="automation_started",
        title="Run automation started",
        detail={"source": source, "auto_agent_review": bool(auto_agent_review)},
    )


def stop_run_automation(
    database_path: Path | str,
    *,
    project_id: str,
    reason: str,
    detail: dict[str, Any] | None = None,
    task_id: str | None = None,
    worker_run_id: str | None = None,
) -> dict[str, Any]:
    def update(state: dict[str, Any]) -> dict[str, Any]:
        state = _normalize_state(project_id, state)
        state.update(
            {
                "status": QUEUE_STATUS_STOPPED,
                "active_task_id": None,
                "active_worker_run_id": None,
                "latest_stop_reason": reason,
            }
        )
        return state

    db.update_portal_setting(database_path, _state_key(project_id), empty_run_automation_state(project_id), update)
    return record_automation_event(
        database_path,
        project_id=project_id,
        kind="automation_stopped",
        title="Run automation stopped",
        detail={"reason": reason, **(detail or {})},
        task_id=task_id,
        worker_run_id=worker_run_id,
        level="warning",
    )


def set_active_automation_run(
    database_path: Path | str,
    *,
    project_id: str,
    task_id: str | None,
    worker_run_id: str | None,
) -> dict[str, Any]:
    def update(state: dict[str, Any]) -> dict[str, Any]:
        state = _normalize_state(project_id, state)
        state["active_task_id"] = task_id
        state["active_worker_run_id"] = worker_run_id
        return state

    return db.update_portal_setting(database_path, _state_key(project_id), empty_run_automation_state(project_id), update)


def list_eligible_estimated_tasks(database_path: Path | str, project_id: str) -> list[dict[str, Any]]:
    return [
        task
        for task in db.list_tasks(database_path)
        if task.get("status") == "Estimated" and task_matches_project(task, project_id) and not db.task_is_archived(task)
    ]


def record_automation_event(
    database_path: Path | str,
    *,
    project_id: str,
    kind: str,
    title: str,
    detail: dict[str, Any] | None = None,
    task_id: str | None = None,
    worker_run_id: str | None = None,
    level: str = "info",
) -> dict[str, Any]:
    event = {
        "kind": kind,
        "title": title,
        "level": level,
        "detail": {"project_id": project_id, **(detail or {})},
        "created_at": _now_iso(),
    }
    def update(state: dict[str, Any]) -> dict[str, Any]:
        state = _normalize_state(project_id, state)
        state_events = list(state.get("events") or [])
        state_events.append(event)
        state["events"] = state_events[-25:]
        return state

    db.update_portal_setting(database_path, _state_key(project_id), empty_run_automation_state(project_id), update)

    if task_id:
        _append_task_automation_event(database_path, task_id, event)
    if worker_run_id:
        run = db.get_worker_run(database_path, worker_run_id)
        db.update_worker_run_metadata(database_path, worker_run_id, {"automation": event})
        db.record_worker_run_event(
            database_path,
            worker_run_id=worker_run_id,
            session_id=run["session_id"],
            task_id=run["task_id"],
            layer="control_plane",
            kind=kind,
            level=level,
            title=title,
            detail=event["detail"],
        )
    return get_run_automation_state(database_path, project_id)


def _append_task_automation_event(database_path: Path | str, task_id: str, event: dict[str, Any]) -> None:
    task = db.get_task(database_path, task_id)
    metadata = dict(task.get("metadata") or {})
    events = list(metadata.get("automation_events") or [])
    events.append(event)
    metadata["automation_events"] = events[-25:]
    db.update_task(database_path, task_id, {"metadata": metadata})


def _normalize_state(project_id: str, state: dict[str, Any]) -> dict[str, Any]:
    normalized = empty_run_automation_state(project_id)
    normalized.update(dict(state or {}))
    normalized["project_id"] = project_id
    normalized["auto_agent_review"] = bool(normalized.get("auto_agent_review"))
    normalized["policy"] = {**DEFAULT_POLICY, **dict(normalized.get("policy") or {})}
    normalized["policy"]["auto_agent_review"] = bool(normalized["auto_agent_review"])
    normalized["events"] = list(normalized.get("events") or [])[-25:]
    return normalized


def _state_key(project_id: str) -> str:
    return f"project_run_automation:{project_id}"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
