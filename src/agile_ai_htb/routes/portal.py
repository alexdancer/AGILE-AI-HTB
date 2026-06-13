from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from agile_ai_htb import db
from agile_ai_htb.auth import require_portal_auth
from agile_ai_htb.guardrails import get_budget_zone


router = APIRouter(dependencies=[Depends(require_portal_auth)])
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")

BOARD_COLUMNS = ["Backlog", "Estimated", "Running", "Review", "Done", "Other"]


@router.get("/dashboard", response_class=HTMLResponse)
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
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "token_total": token_total,
            "daily_cap": daily_cap,
            "current_zone": get_budget_zone(token_total, daily_cap, config),
            "session_count": len(sessions),
            "alarm_count": len(alarms),
            "recent_sessions": list(reversed(sessions[-5:])),
            "recent_alarms": list(reversed(alarms[-5:])),
        },
    )


@router.get("/board", response_class=HTMLResponse)
def board(request: Request):
    tasks = db.list_tasks(request.app.state.settings.database_path)
    grouped = {column: [] for column in BOARD_COLUMNS}
    for task in tasks:
        status = task["status"] if task["status"] in grouped else "Other"
        grouped[status].append(task)
    return templates.TemplateResponse(
        request,
        "board.html",
        {"columns": BOARD_COLUMNS, "tasks_by_status": grouped},
    )


@router.get("/sessions/{session_id}", response_class=HTMLResponse)
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
            "session": artifact["session"],
            "token_totals": token_totals,
            "requires_review": requires_review,
            "zone_timeline": artifact["guardrail_snapshots"],
        },
    )


def _token_totals(artifact: dict[str, Any]) -> dict[str, int]:
    return {
        "prompt_tokens": sum(int(turn.get("prompt_tokens", 0)) for turn in artifact["token_log"]),
        "completion_tokens": sum(int(turn.get("completion_tokens", 0)) for turn in artifact["token_log"]),
        "total_tokens": sum(int(turn.get("total_tokens", 0)) for turn in artifact["token_log"]),
    }


def _current_day_start_iso(timezone: str) -> str:
    if timezone == "local":
        now = datetime.now().astimezone()
    else:
        now = datetime.now(ZoneInfo(timezone))
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(UTC).isoformat()
