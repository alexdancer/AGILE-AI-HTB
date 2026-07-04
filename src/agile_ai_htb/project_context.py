from __future__ import annotations

from pathlib import Path
from typing import Any

from agile_ai_htb import db


def canonical_project_root(root_path: str) -> str:
    return str(Path(str(root_path)).expanduser().resolve())


def project_task_metadata(project: dict[str, Any]) -> dict[str, Any]:
    root_path = canonical_project_root(str(project["root_path"]))
    profile = project.get("profile") or {}
    # Board tasks carry a snapshot of the project binding so launches can reject stale or moved roots later.
    return {
        "connected_project_id": project["id"],
        "project_root_path": root_path,
        "project_profile": profile,
    }


def task_project_id(task: dict[str, Any]) -> str | None:
    value = (task.get("metadata") or {}).get("connected_project_id")
    return str(value) if value else None


def task_project_board_path(task_or_metadata: dict[str, Any]) -> str:
    metadata = task_or_metadata.get("metadata") if "metadata" in task_or_metadata else task_or_metadata
    project_id = (metadata or {}).get("connected_project_id")
    if project_id:
        return f"/projects/{project_id}/board"
    return "/board"


def task_matches_project(task: dict[str, Any], project_id: str) -> bool:
    return task_project_id(task) == project_id


def project_bound_tasks(tasks: list[dict[str, Any]], project_id: str) -> list[dict[str, Any]]:
    return [task for task in tasks if task_matches_project(task, project_id)]


def resolve_task_project(
    database_path: Path | str,
    task: dict[str, Any],
    *,
    expected_project_id: str | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    metadata = task.get("metadata") or {}
    project_id = metadata.get("connected_project_id")
    project_root = metadata.get("project_root_path")
    if expected_project_id and project_id != expected_project_id:
        return None, ["Task is not bound to the selected project board."]
    if not project_id or not project_root:
        return None, ["Task is not bound to a connected project. Recreate it from a project board before launch."]
    try:
        project = db.get_connected_project(database_path, str(project_id))
    except KeyError:
        return None, ["Task is bound to a project that is no longer connected."]
    task_root = canonical_project_root(str(project_root))
    connected_root = canonical_project_root(str(project["root_path"]))
    # Compare canonical paths to catch stale task metadata without treating relative-path spelling as a mismatch.
    if task_root != connected_root:
        return None, ["Task project root does not match the connected project root."]
    return {**project, "root_path": connected_root}, []
