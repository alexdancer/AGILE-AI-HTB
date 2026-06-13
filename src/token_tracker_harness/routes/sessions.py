from __future__ import annotations

import hashlib
import secrets
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from token_tracker_harness import db
from token_tracker_harness.checkpoints import evaluate_checkpoints
from token_tracker_harness.guardrails import get_budget_zone

router = APIRouter()


class SessionStartRequest(BaseModel):
    task_description: str = Field(min_length=1)
    model: str = Field(min_length=1)
    budget: dict[str, Any] | None = None
    guardrail_overrides: dict[str, Any] | None = None


def _database_path(request: Request):
    return request.app.state.settings.database_path


def _guardrails(request: Request):
    return request.app.state.guardrails


@router.post("/session/start")
def start_session(payload: SessionStartRequest, request: Request) -> dict[str, Any]:
    session_api_key = f"sk_sess_{secrets.token_urlsafe(24)}"
    budget = payload.budget or {}
    guardrail_overrides = dict(payload.guardrail_overrides or {})
    if budget:
        guardrail_overrides["budget"] = budget
    session = db.create_session(
        _database_path(request),
        task_description=payload.task_description,
        model=payload.model,
        session_key_hash=_hash_key(session_api_key),
        guardrail_overrides=guardrail_overrides,
    )
    config = _guardrails(request)
    starting_zone = get_budget_zone(
        int(budget.get("daily_used_tokens", 0)),
        _daily_cap_tokens(budget, config),
        config,
    )
    return {
        "session_id": session["id"],
        "session_api_key": session_api_key,
        "starting_zone": starting_zone,
        "report_url": f"/session/{session['id']}/report",
    }


@router.get("/session/{session_id}/report")
def session_report(session_id: str, request: Request) -> dict[str, Any]:
    artifact = _artifact_or_404(request, session_id)
    token_totals = _token_totals(artifact)
    config = _guardrails(request)
    budget = artifact["session"].get("guardrail_overrides", {}).get("budget", {})
    daily_used_tokens = int(budget.get("daily_used_tokens", 0)) + token_totals["total_tokens"]
    current_zone = get_budget_zone(daily_used_tokens, _daily_cap_tokens(budget, config), config)
    return {
        "session": artifact["session"],
        "task_metadata": {
            "description": artifact["session"]["task_description"],
            "model": artifact["session"]["model"],
            "status": artifact["session"]["status"],
        },
        "token_totals": token_totals,
        "current_zone": current_zone,
        "alarms": artifact["alarms"],
        "checkpoints": artifact["checkpoint_results"],
        "tool_breakdown": _tool_breakdown(artifact),
    }


@router.get("/session/{session_id}/artifact")
def session_artifact(session_id: str, request: Request) -> dict[str, Any]:
    return _artifact_or_404(request, session_id)


@router.post("/session/{session_id}/checkpoint/evaluate")
def evaluate_session_checkpoints(session_id: str, request: Request) -> dict[str, Any]:
    artifact = _artifact_or_404(request, session_id)
    results = [result.as_dict() for result in evaluate_checkpoints(artifact, _guardrails(request))]
    for result in results:
        db.record_checkpoint_result(_database_path(request), session_id=session_id, checkpoint=result)
    return {"session_id": session_id, "checkpoint_results": results}


def _artifact_or_404(request: Request, session_id: str) -> dict[str, Any]:
    try:
        return db.build_session_artifact(_database_path(request), session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc


def _token_totals(artifact: dict[str, Any]) -> dict[str, int]:
    return {
        "prompt_tokens": sum(int(turn.get("prompt_tokens", 0)) for turn in artifact["token_log"]),
        "completion_tokens": sum(int(turn.get("completion_tokens", 0)) for turn in artifact["token_log"]),
        "total_tokens": sum(int(turn.get("total_tokens", 0)) for turn in artifact["token_log"]),
    }


def _tool_breakdown(artifact: dict[str, Any]) -> dict[str, dict[str, int]]:
    breakdown: dict[str, dict[str, int]] = {}
    for call in artifact["tool_trace"]:
        tool_name = call["tool_name"]
        breakdown.setdefault(tool_name, {"calls": 0})["calls"] += 1
    return breakdown


def _daily_cap_tokens(budget: dict[str, Any], config) -> int | None:
    if "daily_cap_tokens" in budget:
        return int(budget["daily_cap_tokens"])
    if config.daily_cap.enabled:
        return config.daily_cap.tokens
    return None


def _hash_key(session_api_key: str) -> str:
    return hashlib.sha256(session_api_key.encode("utf-8")).hexdigest()
