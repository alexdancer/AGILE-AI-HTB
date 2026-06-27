from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import os
import secrets

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from agile_ai_htb import db
from agile_ai_htb.adapter_readiness import evaluate_adapter_readiness
from agile_ai_htb.auth import (
    PORTAL_COOKIE_MAX_AGE_SECONDS,
    PORTAL_COOKIE_NAME,
    require_portal_auth,
    sign_portal_cookie,
)
from agile_ai_htb.board_automation import (
    RUN_NEXT_SOURCE,
    RUN_QUEUE_SOURCE,
    get_run_automation_state,
    list_eligible_estimated_tasks,
    record_automation_event,
    set_active_automation_run,
    start_run_automation,
    stop_run_automation,
)
from agile_ai_htb.execution_backend import LocalExecutionBackend
from agile_ai_htb.guardrails import get_budget_zone
from agile_ai_htb.llm import LLMClient, extract_usage, response_to_dict
from agile_ai_htb.operator_config import ensure_secret_placeholder, load_operator_secrets_env, update_operator_config
from agile_ai_htb.project_context import project_bound_tasks
from agile_ai_htb.settings import Settings
from agile_ai_htb.task_launch import DEFAULT_PROXY_URL, TaskLaunchBlocked, launch_task, refresh_task_from_session
from agile_ai_htb.routes.tasks import _ensure_review_task, _run_agent_review
from agile_ai_htb.template_context import portal_template_context
from agile_ai_htb.tracking_modes import NATIVE_USAGE, OBSERVED_ONLY, PROXY_GOVERNED, tracking_mode_view
from agile_ai_htb.worker_model_allowlist import allowed_worker_model_ids
from agile_ai_htb.worker_adapters import (
    detect_worker_adapter,
    discover_worker_models,
    discovered_worker_model_ids,
    verify_worker_adapter,
)


router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).resolve().parents[1] / "templates",
    context_processors=[portal_template_context],
)

BOARD_COLUMNS = ["Estimated", "Running", "Review", "Done", "Blocked"]


class WorkerVerifyRequest(BaseModel):
    model: str = Field(min_length=1)
    proxy_url: str = Field(default=DEFAULT_PROXY_URL, min_length=1)
    tracking_mode: str = Field(default="proxy_governed", pattern="^(proxy_governed|native_usage|observed_only)$")


class ProjectConnectRequest(BaseModel):
    root_path: str = Field(min_length=1)


class WorkerConfigureRequest(BaseModel):
    is_default: bool = False


class TokenBudgetSettingsRequest(BaseModel):
    daily_cap_tokens: int = Field(gt=0)
    session_cap_tokens: int = Field(gt=0)


class ControlPlaneSettingsRequest(BaseModel):
    control_plane_provider: str = Field(min_length=1, pattern="^(openai|anthropic|openai-compatible)$")
    control_plane_model: str = Field(min_length=1)
    control_plane_base_url: str = ""
    control_plane_api_key_env: str = Field(min_length=1, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    apply_to_estimator_breakdown: bool = True

    @field_validator("control_plane_model")
    @classmethod
    def _model_must_not_be_blank(cls, value: str) -> str:
        model = value.strip()
        if not model:
            raise ValueError("model must not be blank")
        return model

    @field_validator("control_plane_base_url")
    @classmethod
    def _base_url_must_be_http_url(cls, value: str) -> str:
        base_url = value.strip()
        if not base_url:
            return ""
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base URL must be an http(s) URL")
        return base_url.rstrip("/")

    @model_validator(mode="after")
    def _compatible_provider_requires_base_url(self) -> "ControlPlaneSettingsRequest":
        if self.control_plane_provider == "openai-compatible" and not self.control_plane_base_url:
            raise ValueError("openai-compatible provider requires a base URL")
        return self


@router.get("/")
def root() -> RedirectResponse:
    return RedirectResponse("/login")


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"active_page": "login"})


@router.post("/login")
def login(request: Request, token: str = Form(...)):
    expected_token = os.getenv(request.app.state.settings.portal_token_env, "")
    if not expected_token or not token:
        raise HTTPException(status_code=401, detail="invalid portal token")
    if not secrets.compare_digest(token, expected_token):
        raise HTTPException(status_code=401, detail="invalid portal token")

    response = RedirectResponse(_default_portal_landing(request.app.state.settings.database_path), status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        PORTAL_COOKIE_NAME,
        sign_portal_cookie(expected_token),
        max_age=PORTAL_COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=request.app.state.settings.portal_cookie_secure,
    )
    return response


@router.post("/logout")
def logout(request: Request):
    response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(
        PORTAL_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=request.app.state.settings.portal_cookie_secure,
    )
    return response


@router.get("/dashboard", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def dashboard(request: Request):
    database_path = request.app.state.settings.database_path
    config = request.app.state.guardrails
    day_start = _current_day_start_iso(request.app.state.settings.timezone)
    token_total = db.total_token_usage(database_path, since=day_start)
    token_breakdown = db.token_usage_breakdown(database_path, since=day_start)
    budget_settings = _effective_budget_settings(database_path, config)
    daily_cap = budget_settings.get("daily_cap_tokens")
    alarms = db.list_alarms(database_path)
    sessions = db.list_sessions(database_path)
    active_sessions = [session for session in sessions if session["status"] in {"active", "running"}]
    open_alarms = [alarm for alarm in alarms if not alarm.get("resolved_at")]
    critical_alarms = [
        alarm
        for alarm in open_alarms
        if str(alarm.get("severity", "")).lower() in {"critical", "high"}
    ]
    tasks = db.list_tasks(database_path)
    ready_task_count = sum(1 for task in tasks if task.get("status") in {"Estimated", "Ready"})
    review_task_count = sum(1 for task in tasks if task.get("status") == "Review")
    has_launchable_worker = any(adapter.get("launchable") for adapter in _worker_adapter_view_models(database_path))
    next_actions = _dashboard_next_actions(
        ready_task_count=ready_task_count,
        review_task_count=review_task_count,
        has_launchable_worker=has_launchable_worker,
        open_alarm_count=len(open_alarms),
        critical_alarm_count=len(critical_alarms),
    )
    accuracy = db.estimation_accuracy(database_path)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "active_page": "dashboard",
            "next_actions": next_actions,
            "token_total": token_total,
            "worker_token_total": token_breakdown["by_category"]["worker_execution"],
            "token_breakdown": token_breakdown,
            "daily_cap": daily_cap,
            "current_zone": get_budget_zone(token_breakdown["by_category"]["worker_execution"], daily_cap, config),
            "session_count": len(sessions),
            "active_session_count": len(active_sessions),
            "alarm_count": len(alarms),
            "open_alarm_count": len(open_alarms),
            "critical_alarm_count": len(critical_alarms),
            "active_sessions": list(reversed(active_sessions[-5:])),
            "recent_sessions": list(reversed(sessions[-5:])),
            "recent_alarms": list(reversed(alarms[-5:])),
            "estimation_accuracy": accuracy,
        },
    )


def _dashboard_next_actions(
    *,
    ready_task_count: int,
    review_task_count: int,
    has_launchable_worker: bool,
    open_alarm_count: int,
    critical_alarm_count: int,
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if not has_launchable_worker:
        actions.append(
            {
                "label": "Set up Worker adapter",
                "detail": "No launchable Worker adapter",
                "href": "/settings/workers",
                "tone": "yellow",
            }
        )
    if review_task_count:
        actions.append(
            {
                "label": f"Review {review_task_count} task{'s' if review_task_count != 1 else ''}",
                "detail": "Awaiting operator review",
                "href": "/board",
                "tone": "purple",
            }
        )
    if ready_task_count:
        actions.append(
            {
                "label": f"Launch {ready_task_count} estimated task{'s' if ready_task_count != 1 else ''}",
                "detail": "Ready on task board",
                "href": "/board",
                "tone": "blue",
            }
        )
    if critical_alarm_count:
        actions.append(
            {
                "label": f"Handle {critical_alarm_count} critical alarm{'s' if critical_alarm_count != 1 else ''}",
                "detail": "High priority alarm inbox",
                "href": "/alarms",
                "tone": "red",
            }
        )
    elif open_alarm_count:
        actions.append(
            {
                "label": f"Review {open_alarm_count} open alarm{'s' if open_alarm_count != 1 else ''}",
                "detail": "Alarm inbox",
                "href": "/alarms",
                "tone": "yellow",
            }
        )
    actions.append(
        {
            "label": "Open task board",
            "detail": "Estimate, launch, refresh, review, or block tasks",
            "href": "/board",
            "tone": "green",
        }
    )
    return actions


@router.get("/projects", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def projects(request: Request):
    return templates.TemplateResponse(
        request,
        "projects.html",
        {
            "active_page": "projects",
            "projects": _project_view_models(request),
            "local_runner_enabled": request.app.state.settings.local_runner_enabled,
        },
    )


@router.get("/projects/{project_id}", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def project_workspace(project_id: str, request: Request):
    database_path = request.app.state.settings.database_path
    try:
        project = db.get_connected_project(database_path, project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="connected project not found") from exc
    project = _project_view_model(request, project)
    summary = _project_workspace_summary(database_path, project)
    return templates.TemplateResponse(
        request,
        "project_workspace.html",
        {
            "active_page": "project_workspace",
            "active_project": project,
            "project": project,
            "summary": summary,
        },
    )


@router.get("/setup", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def setup_overview(request: Request):
    database_path = request.app.state.settings.database_path
    config = request.app.state.guardrails
    settings = request.app.state.settings
    budget_settings = _effective_budget_settings(database_path, config)
    adapters = _worker_adapter_view_models(database_path)
    active_adapter = _active_adapter_for_request(adapters, request)
    projects = db.list_connected_projects(database_path)
    try:
        control_status = db.get_execution_backend_status(database_path, "control_plane_model")
    except KeyError:
        control_status = None
    steps = [
        {
            "name": "Control plane model",
            "state": _control_plane_setup_state(settings, control_status),
            "href": "/settings/control-plane",
            "detail": settings.control_plane_model,
        },
        {
            "name": "Token budget",
            "state": "ready" if budget_settings.get("confirmed") else "needs setup",
            "href": "/settings/budget",
            "detail": f"Daily {budget_settings.get('daily_cap_tokens'):,} · Session {budget_settings.get('session_cap_tokens'):,}" if budget_settings.get("daily_cap_tokens") and budget_settings.get("session_cap_tokens") else "No portal budget confirmed",
        },
        {
            "name": "Worker adapter",
            "state": "ready" if active_adapter and active_adapter.get("launchable") else "needs setup",
            "href": "/settings/workers",
            "detail": active_adapter["name"] if active_adapter else "No adapter selected",
        },
        {
            "name": "Projects",
            "state": "ready" if projects else "optional",
            "href": "/settings/project",
            "detail": projects[0]["name"] if projects else "Connect a project for local Worker runs",
        },
    ]
    ready_to_launch = all(step["state"] == "ready" for step in steps[:3])
    next_step = _next_setup_step(steps, ready_to_launch)
    return templates.TemplateResponse(
        request,
        "setup.html",
        {
            "active_page": "setup",
            "steps": steps,
            "ready_to_launch": ready_to_launch,
            "active_adapter": active_adapter,
            "budget_settings": budget_settings,
            "next_step": next_step,
        },
    )


@router.get("/settings/budget", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def budget_settings(request: Request):
    database_path = request.app.state.settings.database_path
    config = request.app.state.guardrails
    budget = _effective_budget_settings(database_path, config)
    return templates.TemplateResponse(
        request,
        "budget.html",
        {"active_page": "budget", "budget": budget, "error": None},
    )


@router.post("/settings/budget", dependencies=[Depends(require_portal_auth)])
async def save_budget_settings(request: Request):
    payload, wants_html = await _budget_payload_from_request(request)
    database_path = request.app.state.settings.database_path
    saved = db.set_token_budget_settings(
        database_path,
        daily_cap_tokens=payload.daily_cap_tokens,
        session_cap_tokens=payload.session_cap_tokens,
    )
    if wants_html:
        return RedirectResponse("/setup", status_code=status.HTTP_303_SEE_OTHER)
    return saved


@router.get("/board", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def board(request: Request):
    projects = db.list_connected_projects(request.app.state.settings.database_path)
    if projects:
        return RedirectResponse(f"/projects/{projects[0]['id']}/board", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse("/projects", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/projects/{project_id}/board", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def project_board(project_id: str, request: Request):
    database_path = request.app.state.settings.database_path
    try:
        project = db.get_connected_project(database_path, project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="connected project not found") from exc
    return _render_board(request, active_project=_project_view_model(request, project))


@router.post("/projects/{project_id}/run-next", dependencies=[Depends(require_portal_auth)])
def project_run_next(project_id: str, request: Request):
    database_path = request.app.state.settings.database_path
    _ensure_project(database_path, project_id)
    task = _next_eligible_task(database_path, project_id)
    if task is None:
        record_automation_event(
            database_path,
            project_id=project_id,
            kind="automation_skipped",
            title="Run next found no eligible task",
            detail={"reason": "no_eligible_tasks", "source": RUN_NEXT_SOURCE},
        )
        return RedirectResponse(f"/projects/{project_id}/board?error=No%20eligible%20Estimated%20tasks", status_code=303)
    try:
        _launch_project_automation_task(request, project_id=project_id, task=task, source=RUN_NEXT_SOURCE)
    except TaskLaunchBlocked as exc:
        record_automation_event(
            database_path,
            project_id=project_id,
            kind="automation_stopped",
            title="Run next blocked before launch",
            detail={"reason": _automation_stop_reason(exc.task, exc.reasons), "reasons": exc.reasons, "source": RUN_NEXT_SOURCE},
            task_id=exc.task["id"],
            level="warning",
        )
        return RedirectResponse(f"/projects/{project_id}/board?error={';%20'.join(exc.reasons)}", status_code=303)
    return RedirectResponse(f"/projects/{project_id}/board", status_code=303)


@router.post("/projects/{project_id}/queue/start", dependencies=[Depends(require_portal_auth)])
async def project_queue_start(project_id: str, request: Request):
    database_path = request.app.state.settings.database_path
    _ensure_project(database_path, project_id)
    form = await request.form()
    start_run_automation(
        database_path,
        project_id=project_id,
        source=RUN_QUEUE_SOURCE,
        auto_agent_review="auto_agent_review" in form,
    )
    await _advance_project_queue(request, project_id)
    return RedirectResponse(f"/projects/{project_id}/board", status_code=303)


@router.post("/projects/{project_id}/queue/stop", dependencies=[Depends(require_portal_auth)])
def project_queue_stop(project_id: str, request: Request):
    database_path = request.app.state.settings.database_path
    _ensure_project(database_path, project_id)
    stop_run_automation(database_path, project_id=project_id, reason="operator_stop")
    return RedirectResponse(f"/projects/{project_id}/board", status_code=303)


@router.get("/projects/{project_id}/board/status", dependencies=[Depends(require_portal_auth)])
async def project_board_status(project_id: str, request: Request):
    database_path = request.app.state.settings.database_path
    try:
        db.get_connected_project(database_path, project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="connected project not found") from exc
    before = _project_board_counts(database_path, project_id)
    refreshed_ids = _refresh_project_board_tasks(database_path, project_id)
    await _advance_project_queue(request, project_id)
    after = _project_board_counts(database_path, project_id)
    queue_state = get_run_automation_state(database_path, project_id)
    return {
        "project_id": project_id,
        "counts": after,
        "queue": queue_state,
        "has_active_runs": after["Running"] > 0,
        "queue_active": queue_state.get("status") == "running",
        "refreshed_task_ids": refreshed_ids,
        "reload_required": bool(refreshed_ids) or before != after,
    }


def _render_board(request: Request, *, active_project: dict[str, Any] | None = None):
    database_path = request.app.state.settings.database_path
    db.mark_stale_worker_runs_interrupted(database_path)
    if active_project is not None:
        _refresh_project_board_tasks(database_path, str(active_project["id"]))
    tasks = db.list_tasks(database_path)
    if active_project is not None:
        tasks = project_bound_tasks(tasks, str(active_project["id"]))
    grouped = {column: [] for column in BOARD_COLUMNS}
    for task in tasks:
        task = dict(task)
        metadata = dict(task.get("metadata", {}))
        metadata["review_actions_available"] = _review_actions_available(database_path, task)
        if metadata.get("active_worker_run_id"):
            metadata["worker_run_events"] = db.list_worker_run_events(
                database_path,
                worker_run_id=str(metadata["active_worker_run_id"]),
            )[-6:]
        task["metadata"] = metadata
        status = "Estimated" if task["status"] == "Ready" else task["status"] if task["status"] in grouped else "Blocked"
        if status == "Blocked" and task["status"] not in grouped:
            task["metadata"] = {
                **task.get("metadata", {}),
                "blocked_reason": f"Unsupported task status: {task['status']}",
            }
            task["status"] = "Blocked"
        grouped[status].append(task)
    has_demo_tasks = any(str(task["id"]).startswith("DEMO_TASK_2099_") for task in tasks)
    adapters = [adapter for adapter in _worker_adapter_view_models(database_path) if adapter.get("tracking", {}).get("mode") != "observed_only"]
    error = request.query_params.get("error", "")
    board_counts = _board_counts(tasks)
    launchable_adapters = [adapter for adapter in adapters if adapter.get("launchable")]
    board_summary = {
        "counts": board_counts,
        "total_tasks": sum(board_counts.values()),
        "launch_ready": bool(launchable_adapters),
        "active_adapter": launchable_adapters[0] if launchable_adapters else (adapters[0] if adapters else None),
    }
    automation_summary = None
    if active_project is not None:
        project_id = str(active_project["id"])
        counts = board_counts
        queue_state = get_run_automation_state(database_path, project_id)
        automation_summary = {
            "counts": counts,
            "queue": queue_state,
            "eligible_count": len(list_eligible_estimated_tasks(database_path, project_id)),
            "latest_event": (queue_state.get("events") or [None])[-1],
            "live_refresh_enabled": counts["Running"] > 0 or queue_state.get("status") == "running",
        }
    return templates.TemplateResponse(
        request,
        "board.html",
        {
            "active_page": "board",
            "active_project": active_project,
            "columns": BOARD_COLUMNS,
            "tasks_by_status": grouped,
            "has_demo_tasks": has_demo_tasks,
            "has_verified_worker_adapter": db.has_verified_worker_adapter(database_path),
            "adapters": adapters,
            "default_proxy_url": DEFAULT_PROXY_URL,
            "error": error,
            "board_summary": board_summary,
            "board_empty_states": _board_empty_states(active_project, board_summary),
            "automation_summary": automation_summary,
        },
    )


def _project_board_counts(database_path: Path | str, project_id: str) -> dict[str, int]:
    return _board_counts(project_bound_tasks(db.list_tasks(database_path), project_id))


def _project_has_running_work(database_path: Path | str, project_id: str) -> bool:
    project_tasks = project_bound_tasks(db.list_tasks(database_path), project_id)
    if any(task.get("status") == "Running" for task in project_tasks):
        return True
    task_ids = {task["id"] for task in project_tasks}
    return any(
        run.get("status") in {"queued", "running"} and run.get("task_id") in task_ids
        for run in db.list_worker_runs(database_path)
    )


def _board_counts(tasks: list[dict[str, Any]]) -> dict[str, int]:
    counts = {column: 0 for column in BOARD_COLUMNS}
    for task in tasks:
        status_value = "Estimated" if task.get("status") == "Ready" else str(task.get("status") or "Blocked")
        counts[status_value if status_value in counts else "Blocked"] += 1
    return counts


def _board_empty_states(active_project: dict[str, Any] | None, board_summary: dict[str, Any]) -> dict[str, str]:
    intake_target = "the project task intake" if active_project is not None else "a connected project board"
    estimated = f"No Estimated tasks. Add or break down work through {intake_target}; estimated slices are the launch queue."
    if not board_summary.get("launch_ready"):
        estimated += " No launchable Worker adapter is ready yet."
    return {
        "Estimated": estimated,
        "Running": "No Running tasks. Launched Worker slices appear here until their session finishes or is refreshed.",
        "Review": "No Review tasks. Completed Worker runs that need human disposition appear here before Done.",
        "Done": "No Done tasks. Accepted Review work lands here with session evidence preserved.",
        "Blocked": "No Blocked tasks. Guardrail blocks, setup blockers, human Block dispositions, and manual-estimate requirements appear here.",
    }


def _project_workspace_summary(database_path: Path | str, project: dict[str, Any]) -> dict[str, Any]:
    project_id = str(project["id"])
    tasks = project_bound_tasks(db.list_tasks(database_path), project_id)
    counts = _board_counts(tasks)
    adapters = _worker_adapter_view_models(database_path)
    launch_ready = any(adapter.get("launchable") for adapter in adapters)
    capability = project.get("capability") or {}
    next_actions = [
        {
            "label": "Open task board",
            "href": f"/projects/{project_id}/board",
            "tone": "green" if counts["Estimated"] or counts["Review"] else "blue",
            "detail": f"{sum(counts.values())} tasks · {counts['Estimated']} estimated · {counts['Review']} review",
        },
        {
            "label": "Worker setup",
            "href": "/settings/workers",
            "tone": "green" if launch_ready else "yellow",
            "detail": "Launch-ready adapter available" if launch_ready else "Verify a Worker adapter before launch",
        },
    ]
    if counts["Running"]:
        next_actions.append(
            {
                "label": "Running work",
                "href": f"/projects/{project_id}/board",
                "tone": "blue",
                "detail": f"{counts['Running']} running slices need refresh or completion evidence.",
            }
        )
    if counts["Review"]:
        next_actions.append(
            {
                "label": "Review needed",
                "href": f"/projects/{project_id}/board",
                "tone": "yellow",
                "detail": f"{counts['Review']} completed slices need human review disposition.",
            }
        )
    if counts["Blocked"]:
        next_actions.append(
            {
                "label": "Blocked work",
                "href": f"/projects/{project_id}/board",
                "tone": "yellow",
                "detail": f"{counts['Blocked']} slices need guardrail, setup, or manual-estimate attention.",
            }
        )
    next_actions.append(
        {
            "label": "Session evidence",
            "href": "/sessions",
            "tone": "blue",
            "detail": "Review tokens, guardrails, alarms, checkpoints, and Worker timeline evidence",
        }
    )
    return {
        "counts": counts,
        "total_tasks": sum(counts.values()),
        "launch_ready": launch_ready,
        "capability_state": capability.get("state", "unknown"),
        "test_command": (project.get("profile") or {}).get("test_command"),
        "next_actions": next_actions,
    }


def _next_setup_step(steps: list[dict[str, Any]], ready_to_launch: bool) -> dict[str, Any]:
    if ready_to_launch:
        return {"label": "Open task board", "href": "/board", "detail": "Governed Worker launch is ready."}
    next_step = next((step for step in steps[:3] if step["state"] != "ready"), steps[0])
    return {"label": f"Open {next_step['name']}", "href": next_step["href"], "detail": next_step["detail"]}


def _worker_setup_next_action(active_adapter: dict[str, Any] | None, has_projects: bool) -> dict[str, str]:
    if active_adapter is None:
        return {"label": "Choose active adapter", "href": "/settings/workers", "detail": "No Worker adapter is available."}
    if not active_adapter.get("configured"):
        return {"label": "Choose active adapter", "href": f"/settings/workers?adapter_id={active_adapter['id']}", "detail": "Mark an adapter as the active default before launch."}
    if not active_adapter.get("discovered_models"):
        return {"label": "Discover models", "href": f"/settings/workers?adapter_id={active_adapter['id']}", "detail": "Run native discovery so launch controls show approved Worker models."}
    if not active_adapter.get("supported_models"):
        return {"label": "Approve Worker models", "href": f"/settings/workers?adapter_id={active_adapter['id']}", "detail": "Select at least one discovered model for governed launch."}
    if not active_adapter.get("launchable"):
        return {"label": "Verify adapter", "href": f"/settings/workers?adapter_id={active_adapter['id']}", "detail": "Run verification to make this adapter launch-ready."}
    if not has_projects:
        return {"label": "Open local repo", "href": "/projects", "detail": "Connect a project workspace for project-scoped launch."}
    return {"label": "Open task board", "href": "/board", "detail": "Adapter and model selection are launch-ready."}


def _refresh_project_board_tasks(database_path: Path | str, project_id: str) -> list[str]:
    refreshed_ids: list[str] = []
    for task in project_bound_tasks(db.list_tasks(database_path), project_id):
        if task.get("status") != "Running":
            continue
        try:
            refreshed = refresh_task_from_session(database_path, task["id"])
        except KeyError:
            continue
        if refreshed.get("status") != task.get("status") or refreshed.get("metadata") != task.get("metadata"):
            refreshed_ids.append(task["id"])
    return refreshed_ids


def _ensure_project(database_path: Path | str, project_id: str) -> dict[str, Any]:
    try:
        return db.get_connected_project(database_path, project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="connected project not found") from exc


def _next_eligible_task(database_path: Path | str, project_id: str) -> dict[str, Any] | None:
    tasks = list_eligible_estimated_tasks(database_path, project_id)
    return tasks[0] if tasks else None


def _launch_project_automation_task(
    request: Request,
    *,
    project_id: str,
    task: dict[str, Any],
    source: str,
):
    database_path = request.app.state.settings.database_path
    runner = getattr(request.app.state, "task_launch_runner", None)
    automation_metadata = {
        "automation_source": source,
        "automation_policy": get_run_automation_state(database_path, project_id).get("policy"),
    }
    db.update_task(database_path, task["id"], {"metadata": {**task.get("metadata", {}), **automation_metadata}})
    result = launch_task(
        database_path,
        task["id"],
        adapter_id=None,
        model=None,
        proxy_url=DEFAULT_PROXY_URL,
        project_id=project_id,
        runner=runner,
    )
    worker_run_id = result.worker_run["id"] if result.worker_run else None
    record_automation_event(
        database_path,
        project_id=project_id,
        kind="automation_launched",
        title="Run automation launched task",
        detail={"source": source, "task_id": result.task["id"], "worker_run_id": worker_run_id},
        task_id=result.task["id"],
        worker_run_id=worker_run_id,
    )
    if source == RUN_QUEUE_SOURCE:
        set_active_automation_run(
            database_path,
            project_id=project_id,
            task_id=result.task["id"],
            worker_run_id=worker_run_id,
        )
    return result


async def _advance_project_queue(request: Request, project_id: str) -> None:
    database_path = request.app.state.settings.database_path
    queue_state = get_run_automation_state(database_path, project_id)
    if queue_state.get("status") != "running":
        return

    active_run_id = queue_state.get("active_worker_run_id")
    if active_run_id:
        try:
            active_run = db.get_worker_run(database_path, str(active_run_id))
        except KeyError:
            active_run = None
        if active_run and active_run.get("status") in {"queued", "running"}:
            return

    active_task_id = queue_state.get("active_task_id")
    if active_task_id:
        try:
            active_task = db.get_task(database_path, str(active_task_id))
        except KeyError:
            active_task = None
        if active_task and active_task.get("status") == "Running":
            return
        if active_task and active_task.get("status") == "Estimated" and active_task.get("metadata", {}).get("launch_retryable"):
            stop_run_automation(
                database_path,
                project_id=project_id,
                reason="retryable_failure",
                task_id=active_task["id"],
                worker_run_id=str(active_run_id) if active_run_id else None,
            )
            return
        if active_task and active_task.get("status") == "Blocked":
            stop_run_automation(
                database_path,
                project_id=project_id,
                reason="hard_blocker",
                task_id=active_task["id"],
                worker_run_id=str(active_run_id) if active_run_id else None,
            )
            return
        if active_task and active_task.get("status") == "Review":
            active_task = await _maybe_run_auto_agent_review(request, project_id, active_task)

    if get_run_automation_state(database_path, project_id).get("status") != "running":
        return
    if _project_has_running_work(database_path, project_id):
        return

    task = _next_eligible_task(database_path, project_id)
    if task is None:
        stop_run_automation(database_path, project_id=project_id, reason="completed_no_eligible_tasks")
        return
    if get_run_automation_state(database_path, project_id).get("status") != "running":
        return
    if _project_has_running_work(database_path, project_id):
        return
    try:
        _launch_project_automation_task(request, project_id=project_id, task=task, source=RUN_QUEUE_SOURCE)
    except TaskLaunchBlocked as exc:
        stop_run_automation(
            database_path,
            project_id=project_id,
            reason=_automation_stop_reason(exc.task, exc.reasons),
            detail={"reasons": exc.reasons},
            task_id=exc.task["id"],
        )


async def _maybe_run_auto_agent_review(request: Request, project_id: str, task: dict[str, Any]) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    queue_state = get_run_automation_state(database_path, project_id)
    if not queue_state.get("auto_agent_review"):
        return task
    metadata = task.get("metadata") or {}
    if metadata.get("agent_review"):
        return task
    try:
        _ensure_review_task(task, database_path)
    except ValueError as exc:
        record_automation_event(
            database_path,
            project_id=project_id,
            kind="auto_agent_review_skipped",
            title="Auto Agent Review skipped",
            task_id=task["id"],
            worker_run_id=queue_state.get("active_worker_run_id"),
            detail={"review_status": "skipped", "reason": str(exc)},
            level="warning",
        )
        return task
    claimed = db.claim_task_agent_review(
        database_path,
        task["id"],
        {"status": "running", "source": "auto_agent_review", "started_at": datetime.now(UTC).isoformat()},
    )
    if claimed is None:
        return db.get_task(database_path, task["id"])
    reviewed = await _run_agent_review(request, claimed, metadata.get("review_prompt"))
    record_automation_event(
        database_path,
        project_id=project_id,
        kind="auto_agent_review",
        title="Auto Agent Review completed",
        task_id=task["id"],
        worker_run_id=queue_state.get("active_worker_run_id"),
        detail={"review_status": reviewed.get("metadata", {}).get("agent_review", {}).get("status")},
    )
    return reviewed


def _automation_stop_reason(task: dict[str, Any], reasons: list[str]) -> str:
    metadata = task.get("metadata") or {}
    if metadata.get("native_usage_override_ack_required"):
        return "native_usage_ack_required"
    if metadata.get("budget_override_available"):
        return "budget_approval_required"
    if metadata.get("launch_retryable"):
        return "retryable_failure"
    if reasons:
        return "launch_guardrail_blocked"
    return "automation_blocked"


def _review_actions_available(database_path: Path | str, task: dict[str, Any]) -> bool:
    if task.get("status") != "Review":
        return False
    session_id = task.get("session_id")
    if session_id:
        try:
            if db.get_session(database_path, session_id).get("status") == "completed":
                return True
        except KeyError:
            pass
    return any(run.get("status") == "completed" for run in db.list_worker_runs(database_path, task_id=task["id"]))


@router.get("/settings/workers", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def worker_settings(request: Request):
    database_path = request.app.state.settings.database_path
    adapters = _worker_adapter_view_models(database_path)
    active_adapter = _active_adapter_for_request(adapters, request)
    projects = db.list_connected_projects(database_path)
    next_action = _worker_setup_next_action(active_adapter, bool(projects))
    return templates.TemplateResponse(
        request,
        "workers.html",
        {
            "active_page": "workers",
            "adapters": adapters,
            "active_adapter": active_adapter,
            "default_proxy_url": DEFAULT_PROXY_URL,
            "next_action": next_action,
        },
    )


@router.post("/settings/workers/{adapter_id}/configure", dependencies=[Depends(require_portal_auth)])
async def configure_worker_adapter(adapter_id: str, request: Request):
    """Accept adapter settings form fields, update adapter, redirect to workers page."""
    database_path = request.app.state.settings.database_path
    payload, _ = await _config_payload_from_request(request)
    try:
        db.update_worker_adapter(
            database_path,
            adapter_id,
            is_default=payload.is_default,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="worker adapter not found") from exc
    return RedirectResponse("/settings/workers", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/settings/workers/{adapter_id}/allowed-models", dependencies=[Depends(require_portal_auth)])
async def configure_worker_allowed_models(adapter_id: str, request: Request):
    database_path = request.app.state.settings.database_path
    try:
        adapter = db.get_worker_adapter(database_path, adapter_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="worker adapter not found") from exc

    form = await request.form()
    allowed_models = [str(model) for model in form.getlist("allowed_models")]
    discovered_models = discovered_worker_model_ids(adapter)
    invalid = [model for model in allowed_models if model not in discovered_models]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Allowed models must be discovered first: {', '.join(invalid)}")

    config = {**(adapter.get("config") or {}), "allowed_models_configured": True}
    db.update_worker_adapter(database_path, adapter_id, config=config, supported_models=allowed_models)
    return RedirectResponse(f"/settings/workers?adapter_id={adapter_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/settings/workers/{adapter_id}/refresh-diagnostics", dependencies=[Depends(require_portal_auth)])
def refresh_worker_diagnostics(adapter_id: str, request: Request):
    """Force re-detection of adapter binary on PATH."""
    database_path = request.app.state.settings.database_path
    try:
        adapter = db.get_worker_adapter(database_path, adapter_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="worker adapter not found") from exc
    config = dict(adapter.get("config") or {})
    diag = detect_worker_adapter(adapter)
    config["_diagnostics"] = diag
    config["_diagnostics_at"] = datetime.now(UTC).timestamp()
    db.update_worker_adapter(database_path, adapter_id, config=config)
    return RedirectResponse("/settings/workers", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/settings/control-plane", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def control_plane_settings(request: Request):
    settings = request.app.state.settings
    try:
        connection_status = db.get_execution_backend_status(settings.database_path, "control_plane_model")
    except KeyError:
        connection_status = None
    return templates.TemplateResponse(
        request,
        "control_plane.html",
        {
            "active_page": "control_plane",
            "settings": settings,
            "api_key_configured": bool(os.getenv(settings.control_plane_api_key_env)),
            "legacy_api_key_configured": bool(os.getenv(settings.provider_api_key_env)),
            "connection_status": connection_status,
            "shadowed_settings": _control_plane_shadowed_settings(settings),
        },
    )


@router.post("/settings/control-plane", dependencies=[Depends(require_portal_auth)])
async def save_control_plane_settings(request: Request):
    payload, wants_html = await _control_plane_payload_from_request(request)
    current: Settings = request.app.state.settings
    updates: dict[str, Any] = {
        "control_plane_provider": payload.control_plane_provider,
        "control_plane_model": payload.control_plane_model,
        "control_plane_base_url": payload.control_plane_base_url.strip(),
        "control_plane_api_key_env": payload.control_plane_api_key_env,
    }
    if payload.apply_to_estimator_breakdown:
        updates["estimator_model"] = payload.control_plane_model
        updates["task_breakdown_model"] = payload.control_plane_model
    try:
        config = update_operator_config(**updates)
        ensure_secret_placeholder(payload.control_plane_api_key_env)
        load_operator_secrets_env(config)
        _sync_control_plane_env(payload)
    except OSError as exc:
        if wants_html:
            return _control_plane_settings_with_error(request, f"Could not save control-plane config: {exc}")
        return JSONResponse(status_code=500, content={"detail": f"could not save control-plane config: {exc}"})

    new_settings = Settings(
        database_path=current.database_path,
        guardrails_path=current.guardrails_path,
        timezone=current.timezone,
        portal_token_env=current.portal_token_env,
        portal_cookie_secure=current.portal_cookie_secure,
        local_runner_enabled=current.local_runner_enabled,
        provider_api_key_env=current.provider_api_key_env,
        operator_config=config,
    )
    request.app.state.settings = new_settings
    request.app.state.llm_client = LLMClient(new_settings)
    status_record = db.upsert_execution_backend_status(
        new_settings.database_path,
        "control_plane_model",
        name="Control Plane Model",
        online=False,
        details={
            "status": "needs_test",
            "reason": "configuration changed; test required",
            "provider": new_settings.control_plane_provider,
            "model": new_settings.control_plane_model,
            "api_key_env": new_settings.control_plane_api_key_env,
        },
    )
    if wants_html:
        return RedirectResponse("/settings/control-plane", status_code=status.HTTP_303_SEE_OTHER)
    return {
        "settings": {
            "control_plane_provider": new_settings.control_plane_provider,
            "control_plane_model": new_settings.control_plane_model,
            "control_plane_base_url": new_settings.control_plane_base_url,
            "control_plane_api_key_env": new_settings.control_plane_api_key_env,
            "estimator_model": new_settings.estimator_model,
            "task_breakdown_model": new_settings.task_breakdown_model,
        },
        "status": status_record,
        "shadowed_settings": _control_plane_shadowed_settings(new_settings),
    }


@router.post("/settings/control-plane/test", dependencies=[Depends(require_portal_auth)])
async def test_control_plane_connection(request: Request):
    settings = request.app.state.settings
    payload = {
        "model": settings.control_plane_model,
        "messages": [{"role": "user", "content": "Return exactly AGILE_AI_HTB_CONTROL_PLANE_OK."}],
    }
    try:
        response = await request.app.state.llm_client.acompletion(payload)
        status_record = db.upsert_execution_backend_status(
            settings.database_path,
            "control_plane_model",
            name="Control Plane Model",
            online=True,
            details={
                "provider": settings.control_plane_provider,
                "model": settings.control_plane_model,
                "api_key_env": settings.control_plane_api_key_env,
                "usage": extract_usage(response),
                "response": _safe_worker_evidence(response_to_dict(response)),
            },
        )
        return JSONResponse(status_code=200, content={"passed": True, "status": status_record})
    except Exception as exc:
        status_record = db.upsert_execution_backend_status(
            settings.database_path,
            "control_plane_model",
            name="Control Plane Model",
            online=False,
            details={
                "provider": settings.control_plane_provider,
                "model": settings.control_plane_model,
                "api_key_env": settings.control_plane_api_key_env,
                "error_type": type(exc).__name__,
                "error": _safe_worker_evidence(str(exc)),
            },
        )
        return JSONResponse(status_code=503, content={"passed": False, "status": status_record})


@router.get("/settings/project", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def project_settings(request: Request):
    database_path = request.app.state.settings.database_path
    backend = _local_backend(request)
    projects = []
    for project in db.list_connected_projects(database_path):
        capability = backend.project_capability(project) if backend else project.get("capability", {})
        projects.append({**project, "capability": capability})
    backend_status = backend.status() if backend else None
    return templates.TemplateResponse(
        request,
        "project.html",
        {
            "active_page": "project",
            "local_runner_enabled": request.app.state.settings.local_runner_enabled,
            "backend_status": backend_status,
            "projects": projects,
            "error": None,
        },
    )


@router.post("/settings/project/connect", dependencies=[Depends(require_portal_auth)])
async def connect_project_route(request: Request):
    payload, wants_html = await _project_connect_payload_from_request(request)
    backend = _local_backend(request)
    if backend is None:
        message = "Local Runner backend is disabled. Run htb init, then htb serve."
        if wants_html:
            return _project_settings_with_error(request, message)
        return JSONResponse(status_code=409, content={"detail": message})

    result = backend.connect_project(payload.root_path)
    if result.error:
        if wants_html:
            return _project_settings_with_error(request, result.error)
        return JSONResponse(status_code=422, content={"detail": result.error})

    if wants_html and request.query_params.get("redirect") == "workspace" and result.project:
        return RedirectResponse(f"/projects/{result.project['id']}", status_code=status.HTTP_303_SEE_OTHER)
    if wants_html:
        return RedirectResponse("/settings/project", status_code=status.HTTP_303_SEE_OTHER)
    return JSONResponse(status_code=200, content={"project": result.project})


@router.post("/settings/project/{project_id}/read-only-proof", dependencies=[Depends(require_portal_auth)])
async def launch_read_only_proof_route(project_id: str, request: Request):
    backend = _local_backend(request)
    if backend is None:
        return JSONResponse(status_code=409, content={"detail": "Local Runner backend is disabled."})
    database_path = request.app.state.settings.database_path
    project = next((item for item in db.list_connected_projects(database_path) if item["id"] == project_id), None)
    if project is None:
        raise HTTPException(status_code=404, detail="connected project not found")
    capability = backend.project_capability(project)
    if capability.get("state") != "launch_ready":
        return JSONResponse(status_code=409, content={"detail": "Project is not Launch-ready via Local Runner.", "capability": capability})

    task = backend.create_read_only_proof_task({**project, "capability": capability})
    try:
        result = launch_task(
            database_path,
            task["id"],
            adapter_id="opencode",
            model=task.get("recommended_model"),
            proxy_url=DEFAULT_PROXY_URL,
            runner=getattr(request.app.state, "local_runner_proof_runner", None)
            or getattr(request.app.state, "task_launch_runner", None),
        )
    except TaskLaunchBlocked as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"task": exc.task, "launch_guardrails": {"passed": False, "reasons": exc.reasons}},
        )
    return JSONResponse(status_code=200, content=result.as_response())


@router.post("/settings/workers/{adapter_id}/verify", dependencies=[Depends(require_portal_auth)])
async def verify_worker_adapter_route(adapter_id: str, request: Request):
    payload, wants_html = await _worker_verify_payload_from_request(request)
    database_path = request.app.state.settings.database_path
    try:
        _validate_worker_tracking_mode(database_path, adapter_id, payload.tracking_mode)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="worker adapter not found") from exc
    except ValueError as exc:
        if wants_html:
            from urllib.parse import quote

            return RedirectResponse(f"/settings/workers?error={quote(str(exc))}", status_code=status.HTTP_303_SEE_OTHER)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        result = verify_worker_adapter(
            database_path,
            adapter_id,
            model=payload.model,
            proxy_url=payload.proxy_url or DEFAULT_PROXY_URL,
            tracking_mode=payload.tracking_mode,
            runner=getattr(request.app.state, "worker_adapter_verification_runner", None),
            token_recorder=getattr(request.app.state, "worker_adapter_verification_token_recorder", None),
        )
    except KeyError as exc:
        if "worker adapter not found" in str(exc):
            raise HTTPException(status_code=404, detail="worker adapter not found") from exc
        raise HTTPException(
            status_code=422,
            detail=f"worker adapter configuration invalid: missing template variable {exc}",
        ) from exc
    if wants_html:
        return RedirectResponse("/settings/workers", status_code=status.HTTP_303_SEE_OTHER)
    return JSONResponse(
        status_code=200 if result.passed else 409,
        content={
            "passed": result.passed,
            "adapter_id": result.adapter_id,
            "session_id": result.session_id,
            "reasons": result.reasons,
            "evidence": _safe_worker_evidence(result.evidence),
        },
    )


@router.post("/settings/workers/{adapter_id}/discover-models", dependencies=[Depends(require_portal_auth)])
async def discover_worker_models_route(adapter_id: str, request: Request):
    try:
        result = discover_worker_models(
            request.app.state.settings.database_path,
            adapter_id,
            runner=getattr(request.app.state, "worker_model_discovery_runner", None),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="worker adapter not found") from exc
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return RedirectResponse("/settings/workers", status_code=status.HTTP_303_SEE_OTHER)
    return JSONResponse(
        status_code=200 if result.passed else 409,
        content={
            "passed": result.passed,
            "adapter_id": result.adapter_id,
            "models": result.models,
            "reasons": result.reasons,
            "evidence": _safe_worker_evidence(result.evidence),
        },
    )


@router.get("/sessions", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def sessions_index(request: Request):
    database_path = request.app.state.settings.database_path
    config = request.app.state.guardrails
    rows = []
    for session in db.list_sessions(database_path):
        artifact = db.build_session_artifact(database_path, session["id"])
        token_totals = _token_totals(artifact)
        budget = artifact["session"].get("guardrail_overrides", {}).get("budget", {})
        daily_used_tokens = int(budget.get("daily_used_tokens", 0)) + token_totals["total_tokens"]
        daily_cap = _daily_cap_tokens(budget, config)
        rows.append(
            {
                "session": artifact["session"],
                "token_totals": token_totals,
                "current_zone": get_budget_zone(daily_used_tokens, daily_cap, config),
                "alarms": artifact["alarms"],
                "evidence_summary": _session_evidence_summary(artifact),
            }
        )
    return templates.TemplateResponse(
        request,
        "sessions.html",
        {"active_page": "sessions", "sessions": list(reversed(rows))},
    )


@router.get("/sessions/{session_id}", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def session_report_view(session_id: str, request: Request):
    try:
        artifact = db.build_session_artifact(request.app.state.settings.database_path, session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc
    artifact = dict(artifact)
    artifact["worker_run_events"] = [
        {**event, "detail": _safe_worker_evidence(event.get("detail") or {})}
        for event in artifact.get("worker_run_events", [])
    ]

    token_totals = _token_totals(artifact)
    token_breakdown = db.session_token_breakdown(request.app.state.settings.database_path, session_id)
    requires_review = bool(artifact["alarms"]) or any(
        not checkpoint["passed"] for checkpoint in artifact["checkpoint_results"]
    )
    return templates.TemplateResponse(
        request,
        "session_report.html",
        {
            "artifact": artifact,
            "active_page": "sessions",
            "session": artifact["session"],
            "token_totals": token_totals,
            "token_breakdown": token_breakdown,
            "requires_review": requires_review,
            "evidence_summary": _session_evidence_summary(artifact),
            "zone_timeline": artifact["guardrail_snapshots"],
        },
    )


async def _control_plane_payload_from_request(request: Request) -> tuple[ControlPlaneSettingsRequest, bool]:
    content_type = request.headers.get("content-type", "")
    accept = request.headers.get("accept", "")
    wants_html = "text/html" in accept and "application/json" not in accept
    if "application/json" in content_type:
        raw = await request.json()
        try:
            return ControlPlaneSettingsRequest.model_validate(raw or {}), False
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=_validation_error_details(exc)) from exc
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        raw: dict[str, Any] = {key: value for key, value in form.items() if value not in (None, "")}
        raw["apply_to_estimator_breakdown"] = "apply_to_estimator_breakdown" in raw
        try:
            return ControlPlaneSettingsRequest.model_validate(raw), True
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=_validation_error_details(exc)) from exc
    raise HTTPException(status_code=422, detail="control-plane settings are required")


def _validation_error_details(exc: ValidationError) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = [dict(detail) for detail in exc.errors()]
    for detail in details:
        ctx = detail.get("ctx")
        if isinstance(ctx, dict) and "error" in ctx:
            ctx["error"] = str(ctx["error"])
    return details


def _control_plane_setup_state(settings: Settings, control_status: dict[str, Any] | None) -> str:
    if control_status and (control_status.get("details") or {}).get("status") == "needs_test":
        return "needs test"
    if bool(os.getenv(settings.control_plane_api_key_env)) or (control_status and control_status.get("online")):
        return "ready"
    return "needs setup"


def _control_plane_shadowed_settings(settings: Settings) -> dict[str, str]:
    shadowed: dict[str, str] = {}
    checks = {
        "control_plane_provider": ["AGILE_AI_HTB_CONTROL_PROVIDER", "TOKEN_TRACKER_CONTROL_PLANE_PROVIDER"],
        "control_plane_model": ["AGILE_AI_HTB_CONTROL_MODEL", "TOKEN_TRACKER_CONTROL_PLANE_MODEL"],
        "control_plane_base_url": ["AGILE_AI_HTB_CONTROL_BASE_URL", "TOKEN_TRACKER_CONTROL_PLANE_BASE_URL"],
        "control_plane_api_key_env": ["AGILE_AI_HTB_CONTROL_API_KEY_ENV", "TOKEN_TRACKER_CONTROL_PLANE_API_KEY_ENV"],
        "estimator_model": ["AGILE_AI_HTB_ESTIMATOR_MODEL", "TOKEN_TRACKER_ESTIMATOR_MODEL"],
        "task_breakdown_model": ["AGILE_AI_HTB_TASK_BREAKDOWN_MODEL", "TOKEN_TRACKER_TASK_BREAKDOWN_MODEL"],
    }
    for field, env_names in checks.items():
        for env_name in env_names:
            value = os.getenv(env_name)
            if value is not None and value == str(getattr(settings, field)):
                shadowed[field] = env_name
                break
    return shadowed


def _sync_control_plane_env(payload: ControlPlaneSettingsRequest) -> None:
    values = {
        "AGILE_AI_HTB_CONTROL_PROVIDER": payload.control_plane_provider,
        "TOKEN_TRACKER_CONTROL_PLANE_PROVIDER": payload.control_plane_provider,
        "AGILE_AI_HTB_CONTROL_MODEL": payload.control_plane_model,
        "TOKEN_TRACKER_CONTROL_PLANE_MODEL": payload.control_plane_model,
        "AGILE_AI_HTB_CONTROL_BASE_URL": payload.control_plane_base_url,
        "TOKEN_TRACKER_CONTROL_PLANE_BASE_URL": payload.control_plane_base_url,
        "AGILE_AI_HTB_CONTROL_API_KEY_ENV": payload.control_plane_api_key_env,
        "TOKEN_TRACKER_CONTROL_PLANE_API_KEY_ENV": payload.control_plane_api_key_env,
    }
    if payload.apply_to_estimator_breakdown:
        values["AGILE_AI_HTB_ESTIMATOR_MODEL"] = payload.control_plane_model
        values["TOKEN_TRACKER_ESTIMATOR_MODEL"] = payload.control_plane_model
        values["AGILE_AI_HTB_TASK_BREAKDOWN_MODEL"] = payload.control_plane_model
        values["TOKEN_TRACKER_TASK_BREAKDOWN_MODEL"] = payload.control_plane_model
    for name, value in values.items():
        if name in os.environ:
            os.environ[name] = value


def _control_plane_settings_with_error(request: Request, error: str):
    settings = request.app.state.settings
    try:
        connection_status = db.get_execution_backend_status(settings.database_path, "control_plane_model")
    except KeyError:
        connection_status = None
    return templates.TemplateResponse(
        request,
        "control_plane.html",
        {
            "active_page": "control_plane",
            "settings": settings,
            "api_key_configured": bool(os.getenv(settings.control_plane_api_key_env)),
            "legacy_api_key_configured": bool(os.getenv(settings.provider_api_key_env)),
            "connection_status": connection_status,
            "shadowed_settings": _control_plane_shadowed_settings(settings),
            "error": error,
        },
        status_code=500,
    )


async def _budget_payload_from_request(request: Request) -> tuple[TokenBudgetSettingsRequest, bool]:
    content_type = request.headers.get("content-type", "")
    accept = request.headers.get("accept", "")
    wants_html = "text/html" in accept and "application/json" not in accept
    if "application/json" in content_type:
        raw = await request.json()
        try:
            return TokenBudgetSettingsRequest.model_validate(raw or {}), False
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        raw = {key: int(str(value)) for key, value in form.items() if value not in (None, "")}
        try:
            return TokenBudgetSettingsRequest.model_validate(raw), True
        except (ValidationError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="daily and session caps must be positive integers") from exc
    raise HTTPException(status_code=422, detail="budget settings are required")


async def _worker_verify_payload_from_request(request: Request) -> tuple[WorkerVerifyRequest, bool]:
    content_type = request.headers.get("content-type", "")
    accept = request.headers.get("accept", "")
    wants_html = "text/html" in accept and "application/json" not in accept
    if "application/json" in content_type:
        raw = await request.json()
        try:
            return WorkerVerifyRequest.model_validate(raw or {}), False
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        raw = {key: value for key, value in form.items() if value not in (None, "")}
        raw.setdefault("proxy_url", DEFAULT_PROXY_URL)
        try:
            return WorkerVerifyRequest.model_validate(raw), True
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
    raise HTTPException(status_code=422, detail="model is required")


async def _project_connect_payload_from_request(request: Request) -> tuple[ProjectConnectRequest, bool]:
    content_type = request.headers.get("content-type", "")
    accept = request.headers.get("accept", "")
    wants_html = "text/html" in accept and "application/json" not in accept
    if "application/json" in content_type:
        raw = await request.json()
        try:
            return ProjectConnectRequest.model_validate(raw or {}), False
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        raw = {key: value for key, value in form.items() if value not in (None, "")}
        try:
            return ProjectConnectRequest.model_validate(raw), True
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
    raise HTTPException(status_code=422, detail="root_path is required")


async def _config_payload_from_request(request: Request) -> tuple[WorkerConfigureRequest, bool]:
    """Extract worker configure payload from JSON or form-encoded request."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        raw = await request.json()
        try:
            return WorkerConfigureRequest.model_validate(raw or {}), False
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        raw: dict[str, Any] = {key: value for key, value in form.items() if value not in (None, "")}
        raw["is_default"] = "is_default" in raw
        try:
            return WorkerConfigureRequest.model_validate(raw), True
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
    return WorkerConfigureRequest(), True


def _local_backend(request: Request) -> LocalExecutionBackend | None:
    if not request.app.state.settings.local_runner_enabled:
        return None
    backend = getattr(request.app.state, "execution_backend", None)
    if backend is None:
        backend = LocalExecutionBackend(request.app.state.settings.database_path)
        request.app.state.execution_backend = backend
    return backend


def _default_portal_landing(database_path: Path | str) -> str:
    projects = db.list_connected_projects(database_path)
    if projects:
        return f"/projects/{projects[0]['id']}"
    return "/projects"


def _project_view_models(request: Request) -> list[dict[str, Any]]:
    return [_project_view_model(request, project) for project in db.list_connected_projects(request.app.state.settings.database_path)]


def _project_view_model(request: Request, project: dict[str, Any]) -> dict[str, Any]:
    backend = _local_backend(request)
    capability = backend.project_capability(project) if backend else project.get("capability", {})
    return {**project, "capability": capability}


def _project_settings_with_error(request: Request, error: str):
    database_path = request.app.state.settings.database_path
    projects = db.list_connected_projects(database_path)
    backend = _local_backend(request)
    return templates.TemplateResponse(
        request,
        "project.html",
        {
            "active_page": "project",
            "local_runner_enabled": request.app.state.settings.local_runner_enabled,
            "backend_status": backend.status() if backend else None,
            "projects": projects,
            "error": error,
        },
        status_code=422,
    )


def _worker_adapter_view_models(database_path: Path | str) -> list[dict[str, Any]]:
    adapters = []
    for adapter in db.list_worker_adapters(database_path):
        config = adapter.get("config") or {}
        diag = config.get("_diagnostics") or {}
        evidence = adapter.get("verification_evidence") or {}
        readiness = evaluate_adapter_readiness(adapter)
        tracking = readiness.tracking_view()
        available_tracking_modes = _available_worker_tracking_modes(adapter)
        adapters.append(
            {
                **adapter,
                "supported_models": allowed_worker_model_ids(adapter),
                "verification_evidence": _safe_worker_evidence(evidence),
                "diagnostics": diag,
                "launchable": readiness.ui_launchable,
                "discovered_models": discovered_worker_model_ids(adapter),
                "model_discovery": config.get("model_discovery"),
                "tracking_modes": available_tracking_modes,
                "tracking_mode_options": [tracking_mode_view(mode) for mode in available_tracking_modes],
                "connection_type": _worker_connection_type(adapter),
                "tracking": tracking,
                "tracking_label": tracking["label"],
            }
        )
    return adapters


def _available_worker_tracking_modes(adapter: dict[str, Any]) -> list[str]:
    config = adapter.get("config") or {}
    configured = config.get("tracking_modes")
    proxy_capable = _adapter_uses_harness_proxy(adapter)
    native_capable = _adapter_can_emit_native_usage(adapter)
    allowed = _capability_allowed_tracking_modes(proxy_capable=proxy_capable, native_capable=native_capable)
    if configured:
        modes = [_normalize_configured_tracking_mode(mode) for mode in configured]
        modes = [mode for mode in modes if mode in allowed]
        if modes:
            return _dedupe_tracking_modes(modes)

    return _dedupe_tracking_modes([mode for mode in [PROXY_GOVERNED, NATIVE_USAGE, OBSERVED_ONLY] if mode in allowed])


def _capability_allowed_tracking_modes(*, proxy_capable: bool, native_capable: bool) -> set[str]:
    modes: list[str] = []
    if proxy_capable:
        modes.append(PROXY_GOVERNED)
    if native_capable:
        modes.append(NATIVE_USAGE)
    if native_capable or not proxy_capable:
        modes.append(OBSERVED_ONLY)
    return set(modes)


def _normalize_configured_tracking_mode(mode: Any) -> str:
    mode = str(mode)
    if mode == "native":
        return NATIVE_USAGE
    return mode


def _dedupe_tracking_modes(modes: list[str]) -> list[str]:
    deduped: list[str] = []
    for mode in modes:
        if mode not in deduped:
            deduped.append(mode)
    return deduped


def _validate_worker_tracking_mode(database_path: Path | str, adapter_id: str, requested_mode: str) -> None:
    adapter = db.get_worker_adapter(database_path, adapter_id)
    available = _available_worker_tracking_modes(adapter)
    if requested_mode not in available:
        raise ValueError(
            f"Tracking mode {requested_mode!r} is not available for this adapter. Available modes: {', '.join(available)}."
        )


def _worker_connection_type(adapter: dict[str, Any]) -> str:
    if _adapter_uses_harness_proxy(adapter) and not _adapter_can_emit_native_usage(adapter):
        return "API / Proxy Worker"
    if _adapter_uses_harness_proxy(adapter):
        return "API / Proxy-capable CLI Worker"
    return "CLI Worker"


def _adapter_uses_harness_proxy(adapter: dict[str, Any]) -> bool:
    config = adapter.get("config") or {}
    template = config.get("verification_template") or []
    serialized = " ".join(str(part) for part in template)
    return "{proxy_url}" in serialized and "{session_api_key}" in serialized


def _adapter_can_emit_native_usage(adapter: dict[str, Any]) -> bool:
    config = adapter.get("config") or {}
    if config.get("native_verification_template"):
        return True
    return adapter.get("kind") in {"claude_code", "opencode"}


def _active_adapter_for_request(adapters: list[dict[str, Any]], request: Request) -> dict[str, Any] | None:
    requested_id = request.query_params.get("adapter_id")
    if requested_id:
        requested = next((adapter for adapter in adapters if adapter["id"] == requested_id), None)
        if requested:
            return requested
    return next(
        (adapter for adapter in adapters if adapter.get("is_default")),
        next((adapter for adapter in adapters if adapter.get("configured")), adapters[0] if adapters else None),
    )


def _effective_budget_settings(database_path: Path | str, config: Any) -> dict[str, Any]:
    stored = db.get_token_budget_settings(database_path)
    daily_cap = stored.get("daily_cap_tokens")
    session_cap = stored.get("session_cap_tokens")
    if daily_cap is None and config.daily_cap.enabled:
        daily_cap = config.daily_cap.tokens
    if session_cap is None and config.session_cap.enabled:
        session_cap = config.session_cap.tokens
    return {
        "daily_cap_tokens": daily_cap,
        "session_cap_tokens": session_cap,
        "confirmed": bool(stored.get("confirmed")),
    }


def _token_totals(artifact: dict[str, Any]) -> dict[str, int]:
    return {
        "prompt_tokens": sum(int(turn.get("prompt_tokens", 0)) for turn in artifact["token_log"]),
        "completion_tokens": sum(int(turn.get("completion_tokens", 0)) for turn in artifact["token_log"]),
        "total_tokens": sum(int(turn.get("total_tokens", 0)) for turn in artifact["token_log"]),
    }


def _session_evidence_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    checkpoint_results = artifact.get("checkpoint_results") or []
    worker_events = artifact.get("worker_run_events") or []
    worker_runs = artifact.get("worker_runs") or []
    latest_run = worker_runs[-1] if worker_runs else {}
    command_plan = latest_run.get("command_plan") or {}
    command = command_plan.get("command") or []
    if isinstance(command, list):
        launch_target = " ".join(str(part) for part in command) or "missing launch target"
    else:
        launch_target = str(command or "missing launch target")
    metadata = latest_run.get("metadata") or {}
    project_label = (
        metadata.get("connected_project_name")
        or metadata.get("project_name")
        or metadata.get("project_root")
        or metadata.get("workdir")
        or "missing project evidence"
    )
    token_log = artifact.get("token_log") or []
    token_totals = {
        "prompt_tokens": sum(int(turn.get("prompt_tokens", 0)) for turn in token_log),
        "completion_tokens": sum(int(turn.get("completion_tokens", 0)) for turn in token_log),
        "total_tokens": sum(int(turn.get("total_tokens", 0)) for turn in token_log),
    }
    failed_checkpoints = [checkpoint for checkpoint in checkpoint_results if not checkpoint.get("passed")]
    error_events = [event for event in worker_events if event.get("level") == "error"]
    missing_labels = []
    if not worker_runs:
        missing_labels.append("missing Worker Run evidence")
    if not token_log:
        missing_labels.append("missing authoritative token usage")
    if not artifact.get("alarms") and not failed_checkpoints and not error_events:
        missing_labels.append("no review blockers recorded")
    return {
        "task": (artifact.get("session") or {}).get("task_description", "missing task evidence"),
        "selected_project": project_label,
        "launch_target": launch_target,
        "adapter_id": latest_run.get("adapter_id") or "missing Worker Adapter evidence",
        "worker_model": latest_run.get("model") or (artifact.get("session") or {}).get("model") or "missing Worker model evidence",
        "tracking_mode": latest_run.get("tracking_mode") or "missing tracking-mode evidence",
        "status": latest_run.get("status") or (artifact.get("session") or {}).get("status") or "missing status evidence",
        "result": latest_run.get("error_message") or latest_run.get("error_type") or latest_run.get("status") or (artifact.get("session") or {}).get("status") or "missing result evidence",
        "token_totals": token_totals,
        "missing_labels": missing_labels,
        "alarms": len(artifact.get("alarms") or []),
        "checkpoints": len(checkpoint_results),
        "failed_checkpoints": len(failed_checkpoints),
        "worker_runs": len(worker_runs),
        "worker_events": len(worker_events),
        "error_events": len(error_events),
        "requires_review": bool(artifact.get("alarms")) or bool(failed_checkpoints) or bool(error_events),
    }


def _daily_cap_tokens(budget: dict[str, Any], config) -> int | None:
    if "daily_cap_tokens" in budget:
        return int(budget["daily_cap_tokens"])
    if config.daily_cap.enabled:
        return config.daily_cap.tokens
    return None


def _safe_worker_evidence(value: Any, key_hint: str = "") -> Any:
    secret_terms = {"key", "token", "secret", "password", "authorization"}
    if isinstance(value, dict):
        safe = {}
        for key, nested in value.items():
            if any(term in str(key).lower() for term in secret_terms):
                continue
            safe[key] = _safe_worker_evidence(nested, str(key))
        return safe
    if isinstance(value, list):
        return [_safe_worker_evidence(item, key_hint) for item in value]
    if isinstance(value, str):
        if value.startswith("sk_") or "secret" in value.lower():
            return "***REDACTED***"
    return value


def _current_day_start_iso(timezone: str) -> str:
    if timezone == "local":
        now = datetime.now().astimezone()
    else:
        now = datetime.now(ZoneInfo(timezone))
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(UTC).isoformat()
