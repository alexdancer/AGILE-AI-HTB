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

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse

from agile_ai_htb import db
from agile_ai_htb.auth import require_portal_auth
from agile_ai_htb.board_workspace import board_page_context, project_workspace_summary
from agile_ai_htb.task_launch import DEFAULT_PROXY_URL

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
    return index if index.is_file() else None


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
    "/app/{shell_path:path}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_portal_auth)],
)
def react_shell(request: Request, shell_path: str = ""):
    """Serve the React shell index for any React-owned route.

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
