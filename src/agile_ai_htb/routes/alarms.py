from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from agile_ai_htb import db
from agile_ai_htb.auth import require_portal_auth

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")

AlarmAction = Literal["continue", "abort_session", "raise_budget", "adjust_guardrail"]


class ResolveAlarmRequest(BaseModel):
    action: AlarmAction
    payload: dict[str, Any] | None = None


@router.get("/alarms", response_model=None)
def list_alarms(
    request: Request,
    session_id: str | None = None,
    type: str | None = Query(default=None),
    severity: str | None = None,
    resolved: bool | None = None,
):
    alarms = db.list_alarms(
        request.app.state.settings.database_path,
        session_id=session_id,
        alarm_type=type,
        severity=severity,
        resolved=resolved,
    )
    if _wants_html(request):
        require_portal_auth(request)
        open_alarms = [alarm for alarm in alarms if not alarm.get("resolved_at")]
        resolved_alarms = [alarm for alarm in alarms if alarm.get("resolved_at")]
        critical_count = sum(
            1 for alarm in open_alarms if str(alarm.get("severity", "")).lower() in {"critical", "high"}
        )
        warning_count = sum(
            1 for alarm in open_alarms if str(alarm.get("severity", "")).lower() in {"warning", "medium"}
        )
        return templates.TemplateResponse(
            request,
            "alarms.html",
            {
                "active_page": "alarms",
                "open_alarms": open_alarms,
                "resolved_alarms": resolved_alarms,
                "critical_count": critical_count,
                "warning_count": warning_count,
            },
        )
    return {"alarms": alarms}


@router.post("/alarms/{alarm_id}/resolve")
def resolve_alarm(alarm_id: str, payload: ResolveAlarmRequest, request: Request) -> dict[str, Any]:
    try:
        return db.resolve_alarm(
            request.app.state.settings.database_path,
            alarm_id=alarm_id,
            action=payload.action,
            payload=payload.payload,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="alarm not found") from exc


def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept and "application/json" not in accept
