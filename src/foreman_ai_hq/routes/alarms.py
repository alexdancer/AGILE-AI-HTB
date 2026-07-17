from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, ValidationError

from foreman_ai_hq import db
from foreman_ai_hq.auth import require_portal_auth
from foreman_ai_hq.evidence_reporting import safe_evidence

router = APIRouter()

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
        from foreman_ai_hq.routes.react_shell import react_shell_or_missing_build

        return react_shell_or_missing_build()
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
