from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from pydantic import ValidationError

from agile_ai_htb import db
from agile_ai_htb.auth import require_portal_auth
from agile_ai_htb.estimation import EstimatorError, estimate_task
from agile_ai_htb.llm import calculate_cost, extract_usage, response_to_dict
from agile_ai_htb.task_launch import DEFAULT_PROXY_URL, TaskLaunchBlocked, launch_task, refresh_task_from_session

router = APIRouter()
CANONICAL_TASK_STATUSES = {"Estimated", "Ready", "Running", "Review", "Done", "Blocked"}
PositiveStrictInt = Annotated[int, Field(strict=True, gt=0)]
NonNegativeStrictInt = Annotated[int, Field(strict=True, ge=0)]


class TaskCreateRequest(BaseModel):
    description: str = Field(min_length=1)
    status: str | None = None
    estimate_tokens: PositiveStrictInt | None = None
    recommended_model: str | None = None
    actual_tokens: NonNegativeStrictInt | None = None
    session_id: str | None = None
    metadata: dict[str, Any] | None = None


class TaskUpdateRequest(BaseModel):
    description: str | None = None
    status: str | None = None
    estimate_tokens: PositiveStrictInt | None = None
    recommended_model: str | None = None
    actual_tokens: NonNegativeStrictInt | None = None
    session_id: str | None = None
    metadata: dict[str, Any] | None = None


class EstimateRequest(BaseModel):
    description: str = Field(min_length=1)
    remaining_daily_tokens: NonNegativeStrictInt | None = None
    daily_cap_tokens: PositiveStrictInt | None = None


class TaskLaunchRequest(BaseModel):
    adapter_id: str | None = None
    model: str | None = None
    proxy_url: str | None = None
    estimate_tokens: PositiveStrictInt | None = None


@router.post("/tasks")
def create_task(payload: TaskCreateRequest, request: Request) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    status, metadata = _initial_task_status_and_metadata(payload, database_path)
    return db.create_task(
        database_path,
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
            database_path,
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


@router.post("/tasks/{task_id}/launch", dependencies=[Depends(require_portal_auth)])
async def launch_task_endpoint(task_id: str, request: Request):
    payload, wants_html = await _launch_payload_from_request(request)
    database_path = request.app.state.settings.database_path
    runner = getattr(request.app.state, "task_launch_runner", None)
    try:
        result = launch_task(
            database_path,
            task_id,
            adapter_id=payload.adapter_id,
            model=payload.model,
            proxy_url=payload.proxy_url or DEFAULT_PROXY_URL,
            estimate_tokens=payload.estimate_tokens,
            runner=runner,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="task not found") from exc
    except TaskLaunchBlocked as exc:
        if wants_html:
            return RedirectResponse("/board", status_code=303)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "task": exc.task,
                "session": exc.task.get("session_id"),
                "launch_guardrails": {"passed": False, "reasons": exc.reasons},
            },
        )
    if wants_html:
        return RedirectResponse("/board", status_code=303)
    return result.as_response()


@router.post("/tasks/{task_id}/refresh", dependencies=[Depends(require_portal_auth)])
def refresh_task_endpoint(task_id: str, request: Request):
    try:
        return refresh_task_from_session(request.app.state.settings.database_path, task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="task not found") from exc


@router.post("/estimate", dependencies=[Depends(require_portal_auth)])
async def estimate(payload: EstimateRequest, request: Request) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    settings = request.app.state.settings
    try:
        result, llm_response = await estimate_task(
            payload.description,
            request.app.state.guardrails,
            llm_client=request.app.state.llm_client,
            estimator_model=settings.estimator_model,
            remaining_daily_tokens=payload.remaining_daily_tokens,
            daily_cap_tokens=payload.daily_cap_tokens,
        )
    except EstimatorError as exc:
        return db.create_task(
            database_path,
            description=payload.description,
            status="Blocked",
            metadata={
                "blocked_reason": "Estimator unavailable or invalid; manual estimate required.",
                "requires_manual_estimate": True,
                "estimation_source": "manual_required",
                "estimator_failure_type": type(exc).__name__,
            },
        )

    estimation_session = db.create_session(
        database_path,
        task_description=payload.description,
        model=settings.estimator_model,
        session_key_hash=_estimation_session_key_hash(payload.description),
        guardrail_overrides={},
        status="completed",
    )
    usage = extract_usage(llm_response)
    db.record_token_turn(
        database_path,
        session_id=estimation_session["id"],
        usage_kind="estimation",
        model=settings.estimator_model,
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
        cost=calculate_cost(settings.estimator_model, usage["prompt_tokens"], usage["completion_tokens"])
        or 0.0,
        raw_usage={**usage, "response": response_to_dict(llm_response)},
    )
    metadata = {
        "estimation_source": result.source,
        "complexity": result.complexity,
        "confidence": result.confidence,
        "rationale": result.rationale,
        "assumptions": result.assumptions,
        "risk_flags": result.risk_flags,
        "spike_recommendation": result.spike_recommendation,
        "budget_note": result.budget_note,
        "estimation_session_id": estimation_session["id"],
    }
    task = db.create_task(
        database_path,
        description=payload.description,
        status="Estimated",
        estimate_tokens=result.token_estimate,
        recommended_model=result.recommended_model,
        metadata=metadata,
    )
    return {**task, **result.as_dict()}


@router.post("/tasks/estimate-form", dependencies=[Depends(require_portal_auth)])
async def estimate_form(
    description: str = Form(...),
    request: Request = None,  # type: ignore[assignment]
) -> RedirectResponse:
    """HTML form intake: POST description → estimate → redirect to board."""
    await estimate(EstimateRequest(description=description), request)  # type: ignore[arg-type]
    return RedirectResponse("/board", status_code=303)


def _estimation_session_key_hash(description: str) -> str:
    stable_key = f"estimation:v1:{description}"
    return hashlib.sha256(stable_key.encode("utf-8")).hexdigest()


async def _launch_payload_from_request(request: Request) -> tuple[TaskLaunchRequest, bool]:
    content_type = request.headers.get("content-type", "")
    accept = request.headers.get("accept", "")
    wants_html = "text/html" in accept and "application/json" not in accept
    if "application/json" in content_type:
        raw = await request.json()
        try:
            return TaskLaunchRequest.model_validate(raw or {}), False
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        raw: dict[str, Any] = {key: value for key, value in form.items() if value not in (None, "")}
        if "estimate_tokens" in raw:
            estimate_value = raw["estimate_tokens"]
            if not isinstance(estimate_value, str) or not estimate_value.isdecimal() or int(estimate_value) <= 0:
                raise HTTPException(
                    status_code=422,
                    detail=[{"loc": ["body", "estimate_tokens"], "msg": "Input should be a positive integer"}],
                )
            raw["estimate_tokens"] = int(estimate_value)
        raw.setdefault("proxy_url", DEFAULT_PROXY_URL)
        try:
            return TaskLaunchRequest.model_validate(raw), True
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc

    return TaskLaunchRequest(proxy_url=DEFAULT_PROXY_URL), wants_html


def _initial_task_status_and_metadata(
    payload: TaskCreateRequest, database_path: Path | str
) -> tuple[str, dict[str, Any]]:
    metadata = dict(payload.metadata or {})
    has_estimate = payload.estimate_tokens is not None and bool(payload.recommended_model)
    if payload.status is not None:
        if payload.status in CANONICAL_TASK_STATUSES:
            lifecycle_status = _constrain_direct_lifecycle_status(
                database_path,
                requested_status=payload.status,
                session_id=payload.session_id,
                metadata=metadata,
            )
            if lifecycle_status is not None:
                return lifecycle_status, metadata
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


def _canonicalize_task_updates(
    database_path: Path | str, current: dict[str, Any], updates: dict[str, Any]
) -> dict[str, Any]:
    metadata = {**current.get("metadata", {}), **updates.get("metadata", {})}
    estimate_tokens = updates.get("estimate_tokens", current.get("estimate_tokens"))
    recommended_model = updates.get("recommended_model", current.get("recommended_model"))
    if (
        ("estimate_tokens" in updates or "recommended_model" in updates)
        and estimate_tokens is not None
        and recommended_model
    ):
        metadata["estimation_source"] = "manual"
        updates["metadata"] = metadata

    if "status" not in updates:
        return updates

    requested_status = updates["status"]
    if requested_status not in CANONICAL_TASK_STATUSES:
        updates["status"] = "Blocked"
        metadata.setdefault("blocked_reason", f"Unsupported task status: {requested_status}")
        metadata.setdefault("original_status", requested_status)
        updates["metadata"] = metadata
        return updates

    lifecycle_status = _constrain_direct_lifecycle_status(
        database_path,
        requested_status=requested_status,
        session_id=updates.get("session_id", current.get("session_id")),
        metadata=metadata,
    )
    if lifecycle_status is not None:
        updates["status"] = lifecycle_status
        updates["metadata"] = metadata
        return updates

    if requested_status in {"Estimated", "Ready"} and (
        estimate_tokens is None or not recommended_model
    ):
        updates["status"] = "Blocked"
        metadata.setdefault("blocked_reason", "Estimate task before launch.")
        metadata.setdefault("requires_manual_estimate", True)
        metadata.setdefault("requested_status", requested_status)
        updates["metadata"] = metadata
    return updates


def _constrain_direct_lifecycle_status(
    database_path: Path | str,
    *,
    requested_status: str,
    session_id: str | None,
    metadata: dict[str, Any],
) -> str | None:
    if requested_status == "Running":
        metadata.setdefault("blocked_reason", "Use launch endpoint to start tasks.")
        metadata.setdefault("requested_status", requested_status)
        return "Blocked"
    if requested_status in {"Done", "Review"}:
        if session_id and _session_status(database_path, session_id) == "completed":
            return None
        metadata.setdefault("blocked_reason", "Use refresh endpoint to finalize completed sessions.")
        metadata.setdefault("requested_status", requested_status)
        return "Blocked"
    return None


def _session_status(database_path: Path | str, session_id: str) -> str | None:
    try:
        return str(db.get_session(database_path, session_id).get("status"))
    except KeyError:
        return None
