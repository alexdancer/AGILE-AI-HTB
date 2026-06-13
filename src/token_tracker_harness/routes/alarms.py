from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from token_tracker_harness import db

router = APIRouter()

AlarmAction = Literal["continue", "abort_session", "raise_budget", "adjust_guardrail"]


class ResolveAlarmRequest(BaseModel):
    action: AlarmAction
    payload: dict[str, Any] | None = None


@router.get("/alarms")
def list_alarms(
    request: Request,
    session_id: str | None = None,
    type: str | None = Query(default=None),
    severity: str | None = None,
    resolved: bool | None = None,
) -> dict[str, list[dict[str, Any]]]:
    return {
        "alarms": db.list_alarms(
            request.app.state.settings.database_path,
            session_id=session_id,
            alarm_type=type,
            severity=severity,
            resolved=resolved,
        )
    }


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
