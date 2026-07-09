"""FastAPI serving for the React Portal shell.

This module keeps FastAPI as the only backend authority. It:

- serves the built Vite React shell (``/app`` and client sub-routes) and its
  static assets (``/static/react/*``) from a deterministic build directory,
- returns a clear missing-build response instead of a blank shell when the
  frontend has not been built,
- exposes thin authenticated JSON endpoints for the first migrated surface
  (project workspace and project board) that reuse existing view helpers.

Non-migrated Jinja pages and every workflow rule (auth, guardrails, launch,
budget, review disposition) are unchanged and remain the source of truth.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse

from agile_ai_htb import db
from agile_ai_htb.auth import require_portal_auth
from agile_ai_htb.board_workspace import (
    board_page_context,
    project_board_counts,
    project_workspace_summary,
)
from agile_ai_htb.task_launch import DEFAULT_PROXY_URL
from agile_ai_htb.template_context import portal_template_context

router = APIRouter()

_MISSING_BUILD_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Frontend build missing</title>
  </head>
  <body style="font-family: sans-serif; max-width: 40rem; margin: 4rem auto; color: #222;">
    <h1>React Portal shell is not built</h1>
    <p>
      The React Portal assets have not been built yet. Build the frontend with
      <code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code>, or use the
      server-rendered pages instead.
    </p>
    <p><a href="/projects">Open the server-rendered Portal</a></p>
  </body>
</html>
"""


def react_build_dir() -> Path:
    """Deterministic directory the built React shell is served from."""

    return Path(__file__).resolve().parents[1] / "static" / "react"


def _react_index() -> Path | None:
    index = react_build_dir() / "index.html"
    if not index.is_file():
        return None
    return index if _referenced_assets_available(index) else None


def _referenced_assets_available(index: Path) -> bool:
    build_dir = react_build_dir().resolve()
    try:
        html = index.read_text(encoding="utf-8")
    except OSError:
        return False
    asset_paths = re.findall(r'(?:src|href)="(/static/react/[^"]+)"', html)
    if not asset_paths:
        return False
    for asset_path in asset_paths:
        relative = asset_path.removeprefix("/static/react/")
        relative = relative.split("?", 1)[0].split("#", 1)[0]
        target = (build_dir / relative).resolve()
        if (
            (target != build_dir and build_dir not in target.parents)
            or not target.is_file()
        ):
            return False
    return True


@router.get("/static/react/{asset_path:path}")
def react_asset(asset_path: str):
    """Serve built React assets. No auth: these are inert JS/CSS, not data."""

    build_dir = react_build_dir().resolve()
    target = (build_dir / asset_path).resolve()
    # Guard against path traversal escaping the build directory.
    if target != build_dir and build_dir not in target.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if not target.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return FileResponse(target)


@router.get("/app", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
@router.get(
    "/app/projects/{project_id}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_portal_auth)],
)
@router.get(
    "/app/projects/{project_id}/board",
    response_class=HTMLResponse,
    dependencies=[Depends(require_portal_auth)],
)
def react_shell(request: Request, project_id: str | None = None):
    """Serve the React shell index for an explicitly owned route.

    Client-side routing renders the workspace/board from the same ``index.html``.
    When assets are missing we return a clear response, never a blank shell.
    """

    index = _react_index()
    if index is None:
        return HTMLResponse(
            _MISSING_BUILD_HTML,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return FileResponse(index)


@router.get("/api/portal/nav", dependencies=[Depends(require_portal_auth)])
def react_portal_nav(request: Request):
    """Authenticated sidebar navigation context for the React shell.

    Reuses the same ``portal_template_context`` helper that feeds the Jinja
    sidebar in ``base.html`` so the React sidebar and the Jinja sidebar draw
    from a single source of truth. Returns only the fields the sidebar needs.
    """

    context = portal_template_context(request)
    return {
        "portal_auth_required": bool(context.get("portal_auth_required")),
        "sidebar_projects": [
            {
                "id": str(project["id"]),
                "name": project.get("name", ""),
                "task_count": project.get("task_count", 0),
            }
            for project in context.get("sidebar_projects", [])
        ],
    }


@router.get("/api/projects", dependencies=[Depends(require_portal_auth)])
def react_projects_state(request: Request):
    """JSON connected-project list for the shell home / project picker.

    Reuses the same project-list and task-count helpers that feed the Jinja
    projects page; no new schema and no parallel API semantics.
    """

    database_path = request.app.state.settings.database_path
    projects = []
    for project in db.list_connected_projects(database_path):
        view = _project_view_model(request, project)
        counts = project_board_counts(database_path, str(project["id"]))
        projects.append({**view, "counts": counts, "total_tasks": sum(counts.values())})
    return {"projects": projects}


@router.get(
    "/api/projects/{project_id}/workspace",
    dependencies=[Depends(require_portal_auth)],
)
def react_project_workspace_state(project_id: str, request: Request):
    """JSON project workspace state, reusing the existing workspace helper."""

    database_path = request.app.state.settings.database_path
    project = _project_view_model(request, _ensure_project(database_path, project_id))
    summary = project_workspace_summary(database_path, project)
    return {"project": project, "summary": summary}


@router.get(
    "/api/projects/{project_id}/board",
    dependencies=[Depends(require_portal_auth)],
)
def react_project_board_state(project_id: str, request: Request):
    """JSON project board state, reusing the existing board-page context."""

    database_path = request.app.state.settings.database_path
    project = _ensure_project(database_path, project_id)
    if db.project_is_archived(project):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="restore archived project before opening its active board",
        )
    project = _project_view_model(request, project)
    context = board_page_context(
        database_path,
        active_project=project,
        default_proxy_url=DEFAULT_PROXY_URL,
    )
    return {"project": project, **context}


def _ensure_project(database_path, project_id: str) -> dict:
    try:
        return db.get_connected_project(database_path, project_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="connected project not found",
        ) from exc


def _project_view_model(request: Request, project: dict) -> dict:
    # Reuse the Portal's project view model so capability enrichment matches the
    # server-rendered pages. Imported lazily to avoid an import cycle at module
    # load (portal imports from tasks; app wires all routers together).
    from agile_ai_htb.routes.portal import _project_view_model as portal_view_model

    return portal_view_model(request, project)
