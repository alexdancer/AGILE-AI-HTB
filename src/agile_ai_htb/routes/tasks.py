from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agile_ai_htb import db
from agile_ai_htb.estimation import estimate_task

router = APIRouter()
CANONICAL_TASK_STATUSES = {"Estimated", "Ready", "Running", "Review", "Done", "Blocked"}


class TaskCreateRequest(BaseModel):
    description: str = Field(min_length=1)
    status: str | None = None
    estimate_tokens: int | None = None
    recommended_model: str | None = None
    actual_tokens: int | None = None
    session_id: str | None = None
    metadata: dict[str, Any] | None = None


class TaskUpdateRequest(BaseModel):
    description: str | None = None
    status: str | None = None
    estimate_tokens: int | None = None
    recommended_model: str | None = None
    actual_tokens: int | None = None
    session_id: str | None = None
    metadata: dict[str, Any] | None = None


class EstimateRequest(BaseModel):
    description: str = Field(min_length=1)
    remaining_daily_tokens: int | None = None
    daily_cap_tokens: int | None = None


@router.post("/tasks")
def create_task(payload: TaskCreateRequest, request: Request) -> dict[str, Any]:
    status, metadata = _initial_task_status_and_metadata(payload)
    return db.create_task(
        request.app.state.settings.database_path,
        description=payload.description,
        status=status,
        estimate_tokens=payload.estimate_tokens,
        recommended_model=payload.recommended_model,
        actual_tokens=payload.actual_tokens,
        session_id=payload.session_id,
        metadata=metadata,
    )


@router.put("/tasks/{task_id}")
def update_task(task_id: str, payload: TaskUpdateRequest, request: Request) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    try:
        updates = _canonicalize_task_updates(
            db.get_task(database_path, task_id),
            payload.model_dump(exclude_unset=True),
        )
        return db.update_task(
            database_path,
            task_id,
            updates,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="task not found") from exc


@router.post("/estimate")
def estimate(payload: EstimateRequest, request: Request) -> dict[str, Any]:
    return estimate_task(
        payload.description,
        request.app.state.guardrails,
        remaining_daily_tokens=payload.remaining_daily_tokens,
        daily_cap_tokens=payload.daily_cap_tokens,
    ).as_dict()


def _initial_task_status_and_metadata(payload: TaskCreateRequest) -> tuple[str, dict[str, Any]]:
    metadata = dict(payload.metadata or {})
    has_estimate = payload.estimate_tokens is not None and bool(payload.recommended_model)
    if payload.status is not None:
        if payload.status in CANONICAL_TASK_STATUSES:
            if payload.status != "Blocked" and not has_estimate:
                metadata.setdefault("blocked_reason", "Estimate task before launch.")
                metadata.setdefault("requires_manual_estimate", True)
                metadata.setdefault("requested_status", payload.status)
                return "Blocked", metadata
            return payload.status, metadata
        metadata.setdefault("blocked_reason", f"Unsupported task status: {payload.status}")
        metadata.setdefault("original_status", payload.status)
        return "Blocked", metadata
    if has_estimate:
        return "Estimated", metadata
    metadata.setdefault("blocked_reason", "Estimate task before launch.")
    metadata.setdefault("requires_manual_estimate", True)
    return "Blocked", metadata


def _canonicalize_task_updates(current: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    if "status" not in updates:
        return updates

    metadata = {**current.get("metadata", {}), **updates.get("metadata", {})}
    requested_status = updates["status"]
    if requested_status not in CANONICAL_TASK_STATUSES:
        updates["status"] = "Blocked"
        metadata.setdefault("blocked_reason", f"Unsupported task status: {requested_status}")
        metadata.setdefault("original_status", requested_status)
        updates["metadata"] = metadata
        return updates

    estimate_tokens = updates.get("estimate_tokens", current.get("estimate_tokens"))
    recommended_model = updates.get("recommended_model", current.get("recommended_model"))
    if requested_status in {"Estimated", "Ready"} and (
        estimate_tokens is None or not recommended_model
    ):
        updates["status"] = "Blocked"
        metadata.setdefault("blocked_reason", "Estimate task before launch.")
        metadata.setdefault("requires_manual_estimate", True)
        metadata.setdefault("requested_status", requested_status)
        updates["metadata"] = metadata
    return updates
