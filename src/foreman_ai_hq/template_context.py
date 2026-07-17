from __future__ import annotations

from typing import Any

from fastapi import Request

from foreman_ai_hq import db


def portal_template_context(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    auth_context = {"portal_auth_required": settings.portal_auth_required}
    if request.url.path == "/login":
        # The login page must not query or expose project sidebar data before portal auth succeeds.
        return {**auth_context, "sidebar_projects": []}
    database_path = settings.database_path
    task_counts: dict[str, int] = {}
    for task in db.list_tasks(database_path):
        project_id = (task.get("metadata") or {}).get("connected_project_id")
        if project_id:
            task_counts[str(project_id)] = task_counts.get(str(project_id), 0) + 1
    return {
        **auth_context,
        "sidebar_projects": [
            {**project, "task_count": task_counts.get(str(project["id"]), 0)}
            for project in db.list_connected_projects(database_path)
        ]
    }
