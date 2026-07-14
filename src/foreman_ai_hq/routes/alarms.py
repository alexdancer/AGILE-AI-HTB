from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ValidationError

from foreman_ai_hq import db
from foreman_ai_hq.auth import require_portal_auth
from foreman_ai_hq.evidence_reporting import safe_evidence
from foreman_ai_hq.template_context import portal_template_context

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).resolve().parents[1] / "templates",
    context_processors=[portal_template_context],
)

AlarmAction = Literal["continue", "abort_session", "raise_budget", "adjust_guardrail"]


class ResolveAlarmRequest(BaseModel):
    action: AlarmAction
    payload: dict[str, Any] | None = None


RESOLVE_ALARM_OPENAPI_EXTRA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["continue", "abort_session", "raise_budget", "adjust_guardrail"],
                        },
                        "payload": {"type": "object", "additionalProperties": True, "nullable": True},
                    },
                    "required": ["action"],
                }
            },
            "application/x-www-form-urlencoded": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["continue", "abort_session", "raise_budget", "adjust_guardrail"],
                        }
                    },
                    "required": ["action"],
                }
            },
        },
    }
}


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
        # Browser views are protected; JSON polling stays available to API clients.
        require_portal_auth(request)
        from foreman_ai_hq.routes.react_shell import _react_index

        index = _react_index()
        if index is not None:
            return FileResponse(index)
        open_alarms = [alarm for alarm in alarms if not alarm.get("resolved_at")]
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
                "critical_count": critical_count,
                "warning_count": warning_count,
            },
        )
    return {"alarms": alarms}


@router.post("/alarms/{alarm_id}/resolve", response_model=None, openapi_extra=RESOLVE_ALARM_OPENAPI_EXTRA)
async def resolve_alarm(alarm_id: str, request: Request) -> dict[str, Any] | RedirectResponse:
    wants_html = _wants_html(request)
    if wants_html:
        require_portal_auth(request)
    payload = await _resolve_alarm_request(request)
    try:
        result = db.resolve_alarm(
            request.app.state.settings.database_path,
            alarm_id=alarm_id,
            action=payload.action,
            payload=payload.payload,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="alarm not found") from exc
    except ValueError as exc:
        if wants_html:
            return RedirectResponse("/alarms", status_code=status.HTTP_303_SEE_OTHER)
        return {
            "ok": False,
            "error": str(safe_evidence(str(exc), max_length=500)),
            "alarm": None,
            "action": None,
        }
    if wants_html:
        return RedirectResponse("/alarms", status_code=status.HTTP_303_SEE_OTHER)
    return {"ok": True, **result}


async def _resolve_alarm_request(request: Request) -> ResolveAlarmRequest:
    content_type = request.headers.get("content-type", "")
    try:
        # The resolve action can come from the dashboard form or from JSON automation.
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            data: dict[str, Any] = {"action": form.get("action")}
        else:
            data = await request.json()
        return ResolveAlarmRequest.model_validate(data)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="invalid JSON body") from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept and "application/json" not in accept
