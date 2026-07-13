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

import math
from html.parser import HTMLParser
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse

from agile_ai_htb import db
from agile_ai_htb.auth import require_portal_auth
from agile_ai_htb.board_workspace import (
    BOARD_COLUMNS,
    board_page_context,
    project_board_counts,
    project_workspace_summary,
)
from agile_ai_htb.evidence_reporting import safe_evidence
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


def react_shell_available() -> bool:
    """Return whether the complete built React shell can serve the default landing."""

    return _react_index() is not None


class _ReactAssetReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.asset_paths: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del tag
        for name, value in attrs:
            if name in {"src", "href"} and value and value.startswith("/static/react/"):
                self.asset_paths.append(value)


def _referenced_assets_available(index: Path) -> bool:
    build_dir = react_build_dir().resolve()
    try:
        html = index.read_text(encoding="utf-8")
    except OSError:
        return False
    parser = _ReactAssetReferenceParser()
    parser.feed(html)
    asset_paths = parser.asset_paths
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


@router.get("/api/dashboard", dependencies=[Depends(require_portal_auth)])
def react_dashboard_state(request: Request):
    """Bounded read-only dashboard state using the Jinja dashboard calculation."""

    # Imported lazily because portal imports router-adjacent modules while the
    # app wires routes. The Jinja route and React handoff must share this state.
    from agile_ai_htb.routes.portal import _dashboard_context

    context = _dashboard_context(request)
    categories = context["token_breakdown"]["by_category"]
    worker_summary = context["worker_token_summary"]
    components = worker_summary.get("components") or {}
    sidebar_projects = portal_template_context(request).get("sidebar_projects", [])

    return {
        "next_actions": [
            {
                "label": action["label"],
                "detail": action["detail"],
                "href": action["href"],
                "tone": action["tone"],
            }
            for action in context["next_actions"]
        ],
        "budget": {
            "total_tokens": context["budget_token_total"],
            "daily_cap": context["daily_cap"],
            "current_zone": context["current_zone"],
            "since": context["budget_since"],
        },
        "worker_execution": {
            "token_total": context["worker_token_total"],
            "status_split": {
                name: worker_summary["status_split"][name]
                for name in ("completed", "failed_retry", "unknown")
            },
            "components": {
                "available": bool(components.get("available")),
                "items": [
                    {"label": item.get("label", ""), "value": item.get("value", 0)}
                    for item in components.get("items", [])
                ],
                "cost": components.get("cost"),
            },
        },
        "spend": {
            "worker_execution": context["worker_token_total"],
            "agent_review_reporting": categories["reporting_summary"],
            "planning_estimation": categories["task_breakdown"] + categories["control_plane"],
            "setup_verification": categories["adapter_verification"],
            "other": categories["other"],
        },
        "alarms": {
            "total": context["alarm_count"],
            "open": context["open_alarm_count"],
            "critical": context["critical_alarm_count"],
            "recent": [
                {
                    "id": alarm["id"],
                    "type": alarm["type"],
                    "severity": alarm["severity"],
                    "session_id": alarm["session_id"],
                    "recommended_action": alarm["recommended_action"],
                }
                for alarm in context["recent_alarms"]
            ],
        },
        "active_sessions": [
            {
                "id": session["id"],
                "task_description": session["task_description"],
                "model": session["model"],
                "status": session["status"],
            }
            for session in context["active_sessions"]
        ],
        "estimation_accuracy": {
            "completed_count": context["estimation_accuracy"]["completed_count"],
            "median_error_ratio": context["estimation_accuracy"]["median_error_ratio"],
            "within_2x_pct": context["estimation_accuracy"]["within_2x_pct"],
        },
        "projects": [
            _dashboard_project_entry(request, project)
            for project in sidebar_projects
        ],
    }


def _dashboard_project_entry(request: Request, project: dict) -> dict:
    """Project-card fields only; never return workspace path or configuration."""

    capability = _project_view_model(request, project).get("capability") or {}
    return {
        "id": str(project["id"]),
        "name": project.get("name", ""),
        "task_count": project.get("task_count", 0),
        "capability": {"state": capability.get("state", "unknown")},
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
    """Bounded project workspace state derived from existing Portal helpers."""

    database_path = request.app.state.settings.database_path
    stored_project = _ensure_project(database_path, project_id)
    # Stored profile/capability JSON is operator-controlled evidence. Normalize
    # malformed containers before invoking shared capability/summary helpers.
    helper_project = {
        **stored_project,
        "profile": _mapping(stored_project.get("profile")),
        "capability": _mapping(stored_project.get("capability")),
    }
    project = _project_view_model(request, helper_project)
    project = {
        **project,
        "profile": _mapping(project.get("profile")),
        "capability": _mapping(project.get("capability")),
    }
    summary = project_workspace_summary(database_path, project)
    return _react_workspace_projection(project, summary)


def _react_workspace_projection(project: dict, summary: dict) -> dict:
    """Convert broad workspace state into the fixed browser-safe contract."""

    project_id = _workspace_string(project.get("id"), 128)
    profile = _mapping(project.get("profile"))
    capability = _mapping(project.get("capability"))
    summary = _mapping(summary)
    archived_at = _workspace_optional_string(project.get("archived_at"), 64)
    archived = archived_at is not None
    board_href = None if archived else f"/app/projects/{project_id}/board"
    restore_href = f"/projects/{project_id}/restore" if archived else None
    counts = _workspace_counts(summary.get("counts"))

    return {
        "project": {
            "id": project_id,
            "name": _workspace_string(project.get("name"), 200),
            "root_path": _workspace_string(project.get("root_path"), 4096),
            "archived_at": archived_at,
            "capability": {
                "state": _workspace_string(capability.get("state"), 64),
                "label": _workspace_string(capability.get("label"), 200),
                "reasons": _workspace_string_list(capability.get("reasons"), 20, 1000),
            },
            "profile": {
                "git_branch": _workspace_optional_string(profile.get("git_branch"), 500),
                "language_hints": _workspace_string_list(profile.get("language_hints"), 20, 200),
                "framework_hints": _workspace_string_list(profile.get("framework_hints"), 20, 200),
                "package_manager_hints": _workspace_string_list(
                    profile.get("package_manager_hints"), 20, 200
                ),
                "test_command": _workspace_optional_string(profile.get("test_command"), 4000),
                "run_command": _workspace_optional_string(profile.get("run_command"), 4000),
                "relevant_docs": _workspace_string_list(profile.get("relevant_docs"), 50, 1000),
            },
        },
        "summary": {
            "counts": counts,
            "total_tasks": sum(counts.values()),
            "launch_ready": _workspace_bool(summary.get("launch_ready")) and not archived,
            "capability_state": _workspace_string(summary.get("capability_state"), 64),
            "attention_actions": _workspace_attention_actions(
                summary.get("attention_actions"), project_id
            ),
        },
        "controls": {
            "can_open_board": not archived,
            "can_restore": archived,
        },
        "links": {
            "board_href": board_href,
            "task_history_href": f"/projects/{project_id}/task-history",
            "sessions_href": "/sessions",
            "worker_setup_href": "/settings/workers",
            "project_settings_href": "/settings/project",
            "restore_href": restore_href,
        },
    }


def _workspace_string(value, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return str(safe_evidence(value, max_length=limit))[:limit]


def _workspace_optional_string(value, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    text = _workspace_string(value, limit)
    return text or None


def _workspace_string_list(value, item_limit: int, text_limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        _workspace_string(item, text_limit)
        for item in value[:item_limit]
        if isinstance(item, str)
    ]


def _workspace_counts(value) -> dict[str, int]:
    counts = _mapping(value)
    bounded = {}
    for column in BOARD_COLUMNS:
        count = counts.get(column)
        bounded[column] = (
            count
            if isinstance(count, int) and not isinstance(count, bool) and count >= 0
            else 0
        )
    return bounded


def _workspace_bool(value) -> bool:
    return value if isinstance(value, bool) else False


def _workspace_attention_actions(value, project_id: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    actions = []
    for raw_action in value:
        if not isinstance(raw_action, dict):
            continue
        href = _workspace_action_href(raw_action.get("href"), project_id)
        if href is None:
            continue
        actions.append(
            {
                "label": _workspace_string(raw_action.get("label"), 200),
                "detail": _workspace_string(raw_action.get("detail"), 1000),
                "href": href[:2048],
                "tone": _workspace_string(raw_action.get("tone"), 32),
            }
        )
        if len(actions) == 20:
            break
    return actions


def _workspace_action_href(value, project_id: str) -> str | None:
    if not isinstance(value, str):
        return None
    react_board_href = f"/app/projects/{project_id}/board"
    allowed = {
        f"/projects/{project_id}/board": react_board_href,
        react_board_href: react_board_href,
        f"/projects/{project_id}/task-history": f"/projects/{project_id}/task-history",
        "/sessions": "/sessions",
        "/settings/workers": "/settings/workers",
        "/settings/project": "/settings/project",
    }
    return allowed.get(value)


@router.get(
    "/api/projects/{project_id}/board",
    dependencies=[Depends(require_portal_auth)],
)
def react_project_board_state(project_id: str, request: Request):
    """Bounded operator board state; Jinja context stays backend source of truth."""

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
    return _react_board_projection(project, context)


def _react_board_projection(project: dict, context: dict) -> dict:
    """Convert broad Jinja context into an explicit browser-safe allowlist."""

    board_summary = context["board_summary"]
    automation = context.get("automation_summary") or {}
    return {
        "project": {"id": str(project["id"]), "name": project.get("name", "")},
        "columns": list(BOARD_COLUMNS),
        "board_summary": {
            "launch_ready": bool(board_summary.get("launch_ready")),
            "total_tasks": int(board_summary.get("total_tasks") or 0),
            "counts": _canonical_counts(board_summary.get("counts") or {}),
            "archived_count": int(board_summary.get("archived_count") or 0),
            "history_total_tasks": int(board_summary.get("history_total_tasks") or 0),
        },
        "history_href": f"/projects/{project['id']}/task-history",
        "board_empty_states": {
            column: str((context.get("board_empty_states") or {}).get(column) or "")
            for column in BOARD_COLUMNS
        },
        "automation": {
            "counts": _canonical_counts(automation.get("counts") or {}),
            "eligible_count": int(automation.get("eligible_count") or 0),
            "queue": {
                "status": (automation.get("queue") or {}).get("status") or "idle",
                "auto_agent_review": bool((automation.get("queue") or {}).get("auto_agent_review")),
                "latest_stop_reason": (automation.get("queue") or {}).get("latest_stop_reason"),
            },
            "live_refresh_enabled": bool(automation.get("live_refresh_enabled")),
        },
        "adapters": [_react_adapter(adapter) for adapter in context.get("adapters") or []],
        "tasks_by_status": {
            column: [_react_task(task) for task in (context.get("tasks_by_status") or {}).get(column, [])]
            for column in BOARD_COLUMNS
        },
    }


def _canonical_counts(value: dict) -> dict[str, int]:
    return {column: int(value.get(column) or 0) for column in BOARD_COLUMNS}


def _react_adapter(adapter: dict) -> dict:
    tracking = adapter.get("tracking") or {}
    return {
        "id": adapter.get("id"),
        "name": adapter.get("name") or "",
        "is_default": bool(adapter.get("is_default")),
        "launchable": bool(adapter.get("launchable")),
        "allowed_models": list(adapter.get("supported_models") or []),
        "tracking": {
            "mode": tracking.get("mode"),
            "label": adapter.get("tracking_label") or tracking.get("label"),
            "runtime_request_guardrails": tracking.get("runtime_request_guardrails"),
            "accounting": tracking.get("accounting"),
            "budget_authoritative": tracking.get("budget_authoritative"),
            "launchable_for_board": tracking.get("launchable_for_board"),
        },
    }


def _bounded_text(value, limit: int) -> dict:
    text = str(safe_evidence(value or ""))
    return {"text": text[:limit], "truncated": len(text) > limit}


def _bounded_scalar(value, limit: int) -> str:
    return str(safe_evidence(value or ""))[:limit]


def _optional_scalar(value, limit: int) -> str | None:
    return None if value is None else _bounded_scalar(value, limit)


def _optional_number(
    value,
    *,
    integer: bool = False,
    minimum: int | float,
    maximum: int | float,
) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value < minimum or value > maximum:
        return None
    if integer:
        if isinstance(value, float) and not value.is_integer():
            return None
        return int(value)
    return value


def _safe_local_href(value) -> str | None:
    href = _optional_scalar(value, 500)
    return href if href and href.startswith("/") and not href.startswith("//") else None


def _mapping(value) -> dict:
    return value if isinstance(value, dict) else {}


def _react_task(task: dict) -> dict:
    metadata = _mapping(task.get("metadata"))
    launch = _mapping(metadata.get("launch_diagnostic"))
    failure = _mapping(metadata.get("last_launch_failure"))
    review = _mapping(metadata.get("agent_review"))
    findings = review.get("findings") or []
    raw_events = metadata.get("worker_run_events")
    events = [event for event in raw_events if isinstance(event, dict)] if isinstance(raw_events, list) else []
    workdir_evidence = _mapping(metadata.get("workdir_evidence"))
    return {
        "id": task.get("id"),
        "status": task.get("status"),
        "summary": _bounded_text(task.get("description"), 400),
        "estimate_tokens": task.get("estimate_tokens"),
        "actual_tokens": task.get("actual_tokens"),
        "recommended_model": _optional_scalar(task.get("recommended_model"), 200),
        "launch_model": _optional_scalar(metadata.get("launch_model"), 200),
        "session_href": f"/sessions/{task['session_id']}" if task.get("session_id") else None,
        "controls": {
            "can_launch": task.get("status") == "Estimated",
            "can_refresh": task.get("status") == "Running",
            "can_save_review_prompt": bool(metadata.get("review_actions_available")),
            "can_agent_review": bool(metadata.get("review_actions_available")),
            "can_mark_done": bool(metadata.get("review_actions_available")),
            "can_block": bool(metadata.get("review_actions_available")),
            "can_archive": task.get("status") in {"Done", "Blocked"},
            "can_dismiss": task.get("status") == "Estimated",
            "budget_override_available": bool(metadata.get("budget_override_available")),
            "native_usage_override_ack_required": bool(metadata.get("native_usage_override_ack_required")),
            "native_usage_override_ack_text": _optional_scalar(
                metadata.get("native_usage_override_ack_text"), 1000
            ),
            "setup_href": _safe_local_href(launch.get("setup_href")) or "/settings/workers",
        },
        "details": {
            "task_body": _bounded_text(task.get("description"), 12000),
            "token_components": _react_token_components(metadata.get("worker_token_components")),
            "launch": {
                "worker_run_id": _optional_scalar(metadata.get("active_worker_run_id"), 200), "adapter_id": _optional_scalar(metadata.get("launch_adapter_id"), 200),
                "model": _optional_scalar(metadata.get("launch_model"), 200), "tracking_mode": _optional_scalar(metadata.get("tracking_mode"), 100),
                "usage_source": _optional_scalar(metadata.get("usage_source"), 100), "status": _optional_scalar(metadata.get("worker_run_status"), 100),
                "returncode": _optional_number(metadata.get("launch_returncode"), integer=True, minimum=-(2**31), maximum=2**31 - 1), "workdir": _optional_scalar(workdir_evidence.get("configured_workdir"), 1000),
                "error": _bounded_text(metadata.get("launch_error"), 4000),
                "blocked_reason": _bounded_text(metadata.get("launch_blocked_reason"), 4000),
                "retryable_failure": {"returncode": _optional_number(failure.get("returncode"), integer=True, minimum=-(2**31), maximum=2**31 - 1), "summary": _bounded_text(failure.get("error") or failure.get("stderr") or "", 4000)},
                "diagnostic": {"summary": _bounded_text(launch.get("summary"), 4000), "next_action": _bounded_text(launch.get("next_action"), 4000), "setup_href": _safe_local_href(launch.get("setup_href"))},
            },
            "timeline": [{"created_at": _bounded_scalar(event.get("created_at"), 100), "kind": _bounded_scalar(event.get("kind"), 100), "title": _bounded_scalar(event.get("title"), 400), "detail_summary": _bounded_text(event.get("detail_summary") or event.get("detail"), 1000)} for event in events[-6:]],
            "logs": {"stdout": _bounded_text(failure.get("stdout") or metadata.get("launch_stdout"), 4000), "stderr": _bounded_text(failure.get("stderr"), 4000)},
            "review": _react_review(metadata.get("review_prompt"), review, findings),
            "blocked": {"reason": _bounded_text(metadata.get("blocked_reason"), 4000), "requires_manual_estimate": bool(metadata.get("requires_manual_estimate"))},
        },
    }


def _react_token_components(components: dict | None) -> dict:
    components = _mapping(components)
    items = components.get("items")
    return {"available": bool(components.get("available")), "items": [{"key": _bounded_scalar(item.get("key"), 100), "label": _bounded_scalar(item.get("label"), 200), "value": _bounded_scalar(item.get("value"), 400)} for item in (items if isinstance(items, list) else []) if isinstance(item, dict)], "cost": _optional_number(components.get("cost"), minimum=0, maximum=10**12), "turn_count": _optional_number(components.get("turn_count"), integer=True, minimum=0, maximum=10**9)}


def _react_review(prompt, review: dict, findings) -> dict:
    review = _mapping(review)
    token_totals = _mapping(review.get("token_totals"))
    finding_items = findings if isinstance(findings, list) else []
    return {"prompt": _bounded_text(prompt, 4000), "agent_review": {"status": _optional_scalar(review.get("status"), 100), "recommendation": _optional_scalar(review.get("recommendation"), 100), "summary": _bounded_text(review.get("summary"), 4000), "failure": _bounded_text(review.get("error"), 4000), "findings": [{"severity": _bounded_scalar(finding.get("severity"), 40), "message": _bounded_text(finding.get("message"), 1000), "path": _optional_scalar(finding.get("path"), 400), "line": _optional_number(finding.get("line"), integer=True, minimum=0, maximum=10**9)} for finding in finding_items[:20] if isinstance(finding, dict)], "review_session_href": f"/sessions/{_bounded_scalar(review['review_session_id'], 200)}" if review.get("review_session_id") else None, "model": _optional_scalar(review.get("model"), 200), "token_total": _optional_number(token_totals.get("total_tokens"), integer=True, minimum=0, maximum=10**15)}}


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
