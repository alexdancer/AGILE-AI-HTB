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
from agile_ai_htb.guardrails import get_budget_zone
from agile_ai_htb.launch_guardrails import adapter_launchable_for_ui
from agile_ai_htb.task_launch import DEFAULT_PROXY_URL
from agile_ai_htb.worker_adapters import verify_worker_adapter


router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")

BOARD_COLUMNS = ["Estimated", "Ready", "Running", "Review", "Done", "Blocked"]


class WorkerVerifyRequest(BaseModel):
    model: str = Field(min_length=1)
    proxy_url: str = Field(default=DEFAULT_PROXY_URL, min_length=1)


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
    token_total = db.total_token_usage(
        database_path,
        since=_current_day_start_iso(request.app.state.settings.timezone),
    )
    daily_cap = config.daily_cap.tokens if config.daily_cap.enabled else None
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
            "daily_cap": daily_cap,
            "current_zone": get_budget_zone(token_total, daily_cap, config),
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
    return templates.TemplateResponse(
        request,
        "board.html",
        {
            "active_page": "board",
            "columns": BOARD_COLUMNS,
            "tasks_by_status": grouped,
            "has_demo_tasks": has_demo_tasks,
            "has_verified_worker_adapter": db.has_verified_worker_adapter(database_path),
            "default_proxy_url": DEFAULT_PROXY_URL,
        },
    )


@router.get("/settings/workers", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def worker_settings(request: Request):
    adapters = []
    for adapter in db.list_worker_adapters(request.app.state.settings.database_path):
        adapters.append(
            {
                **adapter,
                "verification_evidence": _safe_worker_evidence(adapter.get("verification_evidence", {})),
                "launchable": adapter_launchable_for_ui(adapter),
            }
        )
    return templates.TemplateResponse(
        request,
        "workers.html",
        {"active_page": "workers", "adapters": adapters, "default_proxy_url": DEFAULT_PROXY_URL},
    )


@router.post("/settings/workers/{adapter_id}/verify", dependencies=[Depends(require_portal_auth)])
async def verify_worker_adapter_route(adapter_id: str, request: Request):
    payload, wants_html = await _worker_verify_payload_from_request(request)
    try:
        result = verify_worker_adapter(
            request.app.state.settings.database_path,
            adapter_id,
            model=payload.model,
            proxy_url=payload.proxy_url or DEFAULT_PROXY_URL,
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
            "requires_review": requires_review,
            "zone_timeline": artifact["guardrail_snapshots"],
        },
    )


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
