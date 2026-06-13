from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agile_ai_htb import db
from agile_ai_htb.estimation import estimate_task

router = APIRouter()


class TaskCreateRequest(BaseModel):
    description: str = Field(min_length=1)
    status: str = "Backlog"
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
    return db.create_task(
        request.app.state.settings.database_path,
        description=payload.description,
        status=payload.status,
        estimate_tokens=payload.estimate_tokens,
        recommended_model=payload.recommended_model,
        actual_tokens=payload.actual_tokens,
        session_id=payload.session_id,
        metadata=payload.metadata,
    )


@router.put("/tasks/{task_id}")
def update_task(task_id: str, payload: TaskUpdateRequest, request: Request) -> dict[str, Any]:
    try:
        return db.update_task(
            request.app.state.settings.database_path,
            task_id,
            payload.model_dump(exclude_unset=True),
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
