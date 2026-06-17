from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import os
import secrets

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ValidationError

from agile_ai_htb import db
from agile_ai_htb.auth import (
    PORTAL_COOKIE_MAX_AGE_SECONDS,
    PORTAL_COOKIE_NAME,
    require_portal_auth,
    sign_portal_cookie,
)
from agile_ai_htb.execution_backend import LocalExecutionBackend
from agile_ai_htb.guardrails import get_budget_zone
from agile_ai_htb.launch_guardrails import adapter_launchable_for_ui
from agile_ai_htb.llm import extract_usage, response_to_dict
from agile_ai_htb.task_launch import DEFAULT_PROXY_URL, TaskLaunchBlocked, launch_task
from agile_ai_htb.worker_adapters import detect_worker_adapter, discover_worker_models, verify_worker_adapter


router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")

BOARD_COLUMNS = ["Estimated", "Ready", "Running", "Review", "Done", "Blocked"]


class WorkerVerifyRequest(BaseModel):
    model: str = Field(min_length=1)
    proxy_url: str = Field(default=DEFAULT_PROXY_URL, min_length=1)
    tracking_mode: str = Field(default="proxy_governed", pattern="^(proxy_governed|native_usage)$")


class ProjectConnectRequest(BaseModel):
    root_path: str = Field(min_length=1)


class WorkerConfigureRequest(BaseModel):
    workdir: str = Field(default="", min_length=0)
    is_default: bool = False


class TokenBudgetSettingsRequest(BaseModel):
    daily_cap_tokens: int = Field(gt=0)
    session_cap_tokens: int = Field(gt=0)


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

    response = RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
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
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "active_page": "dashboard",
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
            "state": "ready" if bool(os.getenv(settings.control_plane_api_key_env)) or (control_status and control_status.get("online")) else "needs setup",
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
            "name": "Connected project",
            "state": "ready" if projects else "optional",
            "href": "/settings/project",
            "detail": projects[0]["name"] if projects else "Connect a project for local Worker runs",
        },
    ]
    ready_to_launch = all(step["state"] == "ready" for step in steps[:3])
    return templates.TemplateResponse(
        request,
        "setup.html",
        {
            "active_page": "setup",
            "steps": steps,
            "ready_to_launch": ready_to_launch,
            "active_adapter": active_adapter,
            "budget_settings": budget_settings,
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
    database_path = request.app.state.settings.database_path
    tasks = db.list_tasks(database_path)
    grouped = {column: [] for column in BOARD_COLUMNS}
    for task in tasks:
        task = dict(task)
        status = task["status"] if task["status"] in grouped else "Blocked"
        if status == "Blocked" and task["status"] not in grouped:
            task["metadata"] = {
                **task.get("metadata", {}),
                "blocked_reason": f"Unexpected task status: {task['status']}",
            }
            task["status"] = "Blocked"
        grouped[status].append(task)
    has_demo_tasks = any(str(task["id"]).startswith("DEMO_TASK_2099_") for task in tasks)
    adapters = db.list_worker_adapters(database_path)
    error = request.query_params.get("error", "")
    return templates.TemplateResponse(
        request,
        "board.html",
        {
            "active_page": "board",
            "columns": BOARD_COLUMNS,
            "tasks_by_status": grouped,
            "has_demo_tasks": has_demo_tasks,
            "has_verified_worker_adapter": db.has_verified_worker_adapter(database_path),
            "adapters": adapters,
            "default_proxy_url": DEFAULT_PROXY_URL,
            "error": error,
        },
    )


@router.get("/settings/workers", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def worker_settings(request: Request):
    database_path = request.app.state.settings.database_path
    adapters = _worker_adapter_view_models(database_path)
    active_adapter = _active_adapter_for_request(adapters, request)
    return templates.TemplateResponse(
        request,
        "workers.html",
        {
            "active_page": "workers",
            "adapters": adapters,
            "active_adapter": active_adapter,
            "default_proxy_url": DEFAULT_PROXY_URL,
        },
    )


@router.post("/settings/workers/{adapter_id}/configure", dependencies=[Depends(require_portal_auth)])
async def configure_worker_adapter(adapter_id: str, request: Request):
    """Accept workdir and is_default form fields, update adapter, redirect to workers page."""
    database_path = request.app.state.settings.database_path
    payload, _ = await _config_payload_from_request(request)
    try:
        db.update_worker_adapter(
            database_path,
            adapter_id,
            workdir=payload.workdir if payload.workdir else None,
            is_default=payload.is_default,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="worker adapter not found") from exc
    return RedirectResponse("/settings/workers", status_code=status.HTTP_303_SEE_OTHER)


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
        },
    )


@router.post("/settings/control-plane/test", dependencies=[Depends(require_portal_auth)])
async def test_control_plane_connection(request: Request):
    settings = request.app.state.settings
    payload = {
        "model": settings.control_plane_model,
        "messages": [{"role": "user", "content": "Return exactly AGILE_AI_HTB_CONTROL_PLANE_OK."}],
        "max_tokens": 12,
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
        message = "Local Runner backend is disabled. Start with htb serve --local-runner."
        if wants_html:
            return _project_settings_with_error(request, message)
        return JSONResponse(status_code=409, content={"detail": message})

    result = backend.connect_project(payload.root_path)
    if result.error:
        if wants_html:
            return _project_settings_with_error(request, result.error)
        return JSONResponse(status_code=422, content={"detail": result.error})

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
    try:
        result = verify_worker_adapter(
            request.app.state.settings.database_path,
            adapter_id,
            model=payload.model,
            proxy_url=payload.proxy_url or DEFAULT_PROXY_URL,
            tracking_mode=payload.tracking_mode,
            runner=getattr(request.app.state, "worker_adapter_verification_runner", None),
            token_recorder=getattr(request.app.state, "worker_adapter_verification_token_recorder", None),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="worker adapter not found") from exc
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
            "zone_timeline": artifact["guardrail_snapshots"],
        },
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
        adapters.append(
            {
                **adapter,
                "verification_evidence": _safe_worker_evidence(adapter.get("verification_evidence", {})),
                "diagnostics": diag,
                "launchable": adapter_launchable_for_ui(adapter),
                "model_discovery": config.get("model_discovery"),
                "tracking_modes": config.get("tracking_modes", ["native", "proxy_governed"]),
            }
        )
    return adapters


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
