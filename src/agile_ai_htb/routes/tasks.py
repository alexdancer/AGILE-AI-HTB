from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from pydantic import ValidationError

from agile_ai_htb import db
from agile_ai_htb.auth import require_portal_auth
from agile_ai_htb.estimation import EstimatorError, estimate_task
from agile_ai_htb.llm import LLMClientError, calculate_cost, extract_usage, response_to_dict
from agile_ai_htb.task_launch import DEFAULT_PROXY_URL, TaskLaunchBlocked, launch_task, refresh_task_from_session

router = APIRouter()
CANONICAL_TASK_STATUSES = {"Estimated", "Running", "Review", "Done", "Blocked"}
PositiveStrictInt = Annotated[int, Field(strict=True, gt=0)]
NonNegativeStrictInt = Annotated[int, Field(strict=True, ge=0)]
TOKEN_EVIDENCE_KEYS = {"prompt_tokens", "completion_tokens", "total_tokens"}
SECRET_TEXT_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_.-]+|sk_[A-Za-z0-9_.-]+|Bearer\s+[A-Za-z0-9_.-]+|password\s*[:=]\s*\S+)",
    re.IGNORECASE,
)


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
    adapter_id: str | None = None
    remaining_daily_tokens: NonNegativeStrictInt | None = None
    daily_cap_tokens: PositiveStrictInt | None = None


class TaskLaunchRequest(BaseModel):
    adapter_id: str | None = None
    model: str | None = None
    proxy_url: str | None = None
    estimate_tokens: PositiveStrictInt | None = None
    budget_override: bool = False
    native_budget_acknowledged: bool = False


class TaskReviewActionRequest(BaseModel):
    action: str = Field(pattern="^(save_prompt|agent_review|mark_done|block)$")
    review_prompt: str | None = None
    blocked_reason: str | None = None


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
            budget_override=payload.budget_override,
            native_budget_acknowledged=payload.native_budget_acknowledged,
            runner=runner,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="task not found") from exc
    except TaskLaunchBlocked as exc:
        if wants_html:
            if exc.task.get("metadata", {}).get("launch_retryable"):
                return RedirectResponse("/board", status_code=303)
            from urllib.parse import quote
            error_msg = "; ".join(exc.reasons) if exc.reasons else "Launch failed."
            return RedirectResponse(f"/board?error={quote(error_msg)}", status_code=303)
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
        database_path = request.app.state.settings.database_path
        db.mark_stale_worker_runs_interrupted(database_path)
        task = refresh_task_from_session(database_path, task_id)
        if "text/html" in request.headers.get("accept", ""):
            return RedirectResponse("/board", status_code=303)
        return task
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="task not found") from exc


@router.post("/tasks/{task_id}/review", dependencies=[Depends(require_portal_auth)])
async def review_task_endpoint(task_id: str, request: Request):
    payload, wants_html = await _review_action_payload_from_request(request)
    database_path = request.app.state.settings.database_path
    try:
        task = db.get_task(database_path, task_id)
        _ensure_review_task(task, database_path)
        if payload.action == "save_prompt":
            updated = _save_review_prompt(database_path, task, payload.review_prompt)
        elif payload.action == "mark_done":
            updated = _mark_review_done(database_path, task)
        elif payload.action == "block":
            updated = _block_review_task(database_path, task, payload.blocked_reason)
        elif payload.action == "agent_review":
            updated = await _run_agent_review(request, task, payload.review_prompt)
        else:  # pragma: no cover - pydantic validation prevents this
            raise HTTPException(status_code=422, detail="unsupported review action")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="task not found") from exc
    except ValueError as exc:
        if wants_html:
            from urllib.parse import quote

            return RedirectResponse(f"/board?error={quote(str(exc))}", status_code=303)
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if wants_html:
        return RedirectResponse("/board", status_code=303)
    return updated


@router.post("/estimate", dependencies=[Depends(require_portal_auth)])
async def estimate(payload: EstimateRequest, request: Request) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    settings = request.app.state.settings
    try:
        result, llm_response = await estimate_task(
            payload.description,
            request.app.state.guardrails,
            llm_client=request.app.state.llm_client,
            estimator_model=settings.control_plane_model,
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
        model=settings.control_plane_model,
        session_key_hash=_estimation_session_key_hash(payload.description),
        guardrail_overrides={},
        status="completed",
    )
    usage = extract_usage(llm_response)
    db.record_token_turn(
        database_path,
        session_id=estimation_session["id"],
        usage_kind="estimation",
        model=settings.control_plane_model,
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
        cost=calculate_cost(settings.control_plane_model, usage["prompt_tokens"], usage["completion_tokens"])
        or 0.0,
        raw_usage={**usage, "response": response_to_dict(llm_response)},
    )
    recommended_model, model_metadata = _constrained_recommended_model(
        database_path,
        result.recommended_model,
        adapter_id=payload.adapter_id,
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
        **_markdown_breakdown_metadata(payload.description),
        **model_metadata,
    }
    task = db.create_task(
        database_path,
        description=payload.description,
        status="Estimated",
        estimate_tokens=result.token_estimate,
        recommended_model=recommended_model,
        metadata=metadata,
    )
    return {**task, **result.as_dict(), "recommended_model": recommended_model}


def _constrained_recommended_model(
    database_path: Path | str,
    recommended_model: str,
    *,
    adapter_id: str | None,
) -> tuple[str, dict[str, Any]]:
    adapter = None
    if adapter_id:
        try:
            adapter = db.get_worker_adapter(database_path, adapter_id)
        except KeyError:
            adapter = None
    else:
        adapters = db.list_worker_adapters(database_path)
        adapter = next((item for item in adapters if item.get("is_default")), adapters[0] if adapters else None)
    if not adapter:
        return recommended_model, {"worker_model_constraint": {"state": "no_adapter", "original_model": recommended_model}}
    models = adapter.get("supported_models") or []
    metadata = {
        "worker_model_constraint": {
            "state": "constrained_by_discovered_models",
            "adapter_id": adapter["id"],
            "available_models": models,
            "original_model": recommended_model,
        }
    }
    if not models:
        metadata["worker_model_constraint"]["state"] = "no_discovered_models"
        return recommended_model, metadata
    if recommended_model in models:
        metadata["worker_model_constraint"]["selected_model"] = recommended_model
        return recommended_model, metadata
    metadata["worker_model_constraint"].update({"selected_model": models[0], "reason": "estimator_model_not_discovered"})
    return str(models[0]), metadata


@router.post("/tasks/estimate-form", dependencies=[Depends(require_portal_auth)])
async def estimate_form(
    request: Request,
    description: str = Form(""),
    markdown_file: UploadFile | None = File(None),
) -> RedirectResponse:
    """HTML form intake: POST plain text or Markdown → estimate → redirect to board."""
    try:
        normalized_description, intake_metadata = await _description_from_intake_form(description, markdown_file)
    except ValueError as exc:
        from urllib.parse import quote

        return RedirectResponse(f"/board?error={quote(str(exc))}", status_code=303)

    task = await estimate(EstimateRequest(description=normalized_description), request)
    if intake_metadata:
        db.update_task(
            request.app.state.settings.database_path,
            task["id"],
            {"metadata": {**task.get("metadata", {}), **intake_metadata}},
        )
    return RedirectResponse("/board", status_code=303)


async def _description_from_intake_form(
    description: str, markdown_file: UploadFile | None
) -> tuple[str, dict[str, Any]]:
    if markdown_file and markdown_file.filename:
        filename = Path(markdown_file.filename).name
        if Path(filename).suffix.lower() != ".md":
            raise ValueError("Upload a Markdown .md file or paste Markdown text.")
        raw = await markdown_file.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Markdown upload must be UTF-8 text.") from exc
        normalized = text.strip()
        if not normalized:
            raise ValueError("Markdown upload is empty.")
        return normalized, {"intake_source": "markdown_upload", "intake_filename": filename}

    normalized = description.strip()
    if not normalized:
        raise ValueError("Describe a coding task or upload a Markdown .md file.")
    metadata = {"intake_source": "markdown_paste"} if _looks_like_markdown(normalized) else {"intake_source": "plain_text"}
    return normalized, metadata


def _looks_like_markdown(text: str) -> bool:
    markdown_markers = ("# ", "## ", "- [ ]", "- [x]", "```", "\n- ", "\n* ", "\n1. ")
    return any(marker in text for marker in markdown_markers)


async def _review_action_payload_from_request(request: Request) -> tuple[TaskReviewActionRequest, bool]:
    content_type = request.headers.get("content-type", "")
    accept = request.headers.get("accept", "")
    wants_html = "text/html" in accept and "application/json" not in accept
    if "application/json" in content_type:
        try:
            return TaskReviewActionRequest.model_validate(await request.json()), False
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        raw = {key: value for key, value in form.items() if value is not None}
        try:
            return TaskReviewActionRequest.model_validate(raw), True
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
    try:
        return TaskReviewActionRequest.model_validate({}), wants_html
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


def _ensure_review_task(task: dict[str, Any], database_path: Path | str) -> None:
    if task.get("status") != "Review":
        raise ValueError("Review actions are only available for tasks in Review.")
    session_id = task.get("session_id")
    has_completed_session = bool(session_id) and _session_status(database_path, session_id) == "completed"
    has_completed_worker_run = any(
        run.get("status") == "completed" for run in db.list_worker_runs(database_path, task_id=task["id"])
    )
    if not has_completed_session and not has_completed_worker_run:
        raise ValueError("Review actions require completed Worker Run evidence.")


def _save_review_prompt(database_path: Path | str, task: dict[str, Any], prompt: str | None) -> dict[str, Any]:
    metadata = {**task.get("metadata", {})}
    metadata["review_prompt"] = (prompt or "").strip()
    metadata["review_prompt_updated_at"] = _now_iso()
    return db.update_task(database_path, task["id"], {"metadata": metadata})


def _mark_review_done(database_path: Path | str, task: dict[str, Any]) -> dict[str, Any]:
    metadata = {
        **task.get("metadata", {}),
        "review_decision": "accepted",
        "reviewed_by": "operator",
        "reviewed_at": _now_iso(),
    }
    return db.update_task(database_path, task["id"], {"status": "Done", "metadata": metadata})


def _block_review_task(database_path: Path | str, task: dict[str, Any], reason: str | None) -> dict[str, Any]:
    blocked_reason = (reason or "").strip()
    if not blocked_reason:
        raise ValueError("Blocked Review tasks require a reason.")
    metadata = {
        **task.get("metadata", {}),
        "review_decision": "blocked",
        "blocked_reason": blocked_reason,
        "reviewed_by": "operator",
        "reviewed_at": _now_iso(),
    }
    return db.update_task(database_path, task["id"], {"status": "Blocked", "metadata": metadata})


async def _run_agent_review(request: Request, task: dict[str, Any], prompt: str | None) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    settings = request.app.state.settings
    metadata = {**task.get("metadata", {})}
    review_prompt = (prompt or metadata.get("review_prompt") or "").strip()
    if review_prompt:
        metadata["review_prompt"] = review_prompt
        metadata["review_prompt_updated_at"] = _now_iso()

    review_session = db.create_session(
        database_path,
        task_description=f"Agent review for task {task['id']}: {task['description']}",
        model=settings.control_plane_model,
        session_key_hash=_agent_review_session_key_hash(task["id"], _now_iso()),
        guardrail_overrides={"spend_category": "agent_review", "task_id": task["id"]},
        status="completed",
    )
    llm_request = {
        "model": settings.control_plane_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the AGILE-AI-HTB control-plane reviewer. Review completed Worker Run evidence. "
                    "Return compact JSON with keys summary, recommendation, findings. "
                    "recommendation must be approve, needs_changes, or block. findings is an array of objects "
                    "with severity and message, optionally path and line. Do not include secrets."
                ),
            },
            {"role": "user", "content": _agent_review_prompt(task, review_prompt, database_path)},
        ],
        "temperature": 0,
        "max_tokens": 700,
    }
    try:
        response = await request.app.state.llm_client.acompletion(llm_request)
        response_body = response_to_dict(response)
        usage = extract_usage(response_body)
        db.record_token_turn(
            database_path,
            session_id=review_session["id"],
            usage_kind="reporting",
            model=settings.control_plane_model,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            cost=calculate_cost(settings.control_plane_model, usage["prompt_tokens"], usage["completion_tokens"])
            or 0.0,
            raw_usage={**usage, "spend_category": "agent_review", "response": _safe_review_value(response_body)},
        )
        review = _parse_agent_review(_completion_content(response_body))
        review.update(
            {
                "status": "completed",
                "reviewed_at": _now_iso(),
                "review_session_id": review_session["id"],
                "model": settings.control_plane_model,
            }
        )
    except (LLMClientError, RuntimeError, TypeError, ValueError) as exc:
        db.update_session_status(database_path, review_session["id"], "failed")
        review = {
            "status": "failed",
            "summary": "Agent Review failed; operator can still mark done or block manually.",
            "findings": [],
            "recommendation": "needs_changes",
            "reviewed_at": _now_iso(),
            "review_session_id": review_session["id"],
            "model": settings.control_plane_model,
            "error_type": type(exc).__name__,
            "error": _safe_review_value(str(exc)),
        }

    metadata["agent_review"] = review
    return db.update_task(database_path, task["id"], {"metadata": metadata})


def _agent_review_prompt(task: dict[str, Any], review_prompt: str, database_path: Path | str) -> str:
    artifact: dict[str, Any] = {}
    worker_runs: list[dict[str, Any]] = []
    if task.get("session_id"):
        try:
            artifact = db.build_session_artifact(database_path, task["session_id"])
        except KeyError:
            artifact = {}
    if artifact.get("worker_runs"):
        worker_runs = artifact.get("worker_runs", [])
    else:
        worker_runs = db.list_worker_runs(database_path, task_id=task["id"])
    evidence = {
        "task": {
            "id": task.get("id"),
            "description": task.get("description"),
            "status": task.get("status"),
            "estimate_tokens": task.get("estimate_tokens"),
            "actual_tokens": task.get("actual_tokens"),
            "session_id": task.get("session_id"),
            "metadata": task.get("metadata", {}),
        },
        "operator_focus": review_prompt,
        "session": artifact.get("session", {}),
        "token_log": artifact.get("token_log", [])[-5:],
        "checkpoint_results": artifact.get("checkpoint_results", [])[-5:],
        "worker_runs": worker_runs[-3:],
    }
    return json.dumps(_safe_review_value(evidence), sort_keys=True)[:6000]


def _parse_agent_review(content: str) -> dict[str, Any]:
    parsed: Any
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {"summary": content.strip()}
    if not isinstance(parsed, dict):
        parsed = {"summary": str(parsed)}
    findings = parsed.get("findings") if isinstance(parsed.get("findings"), list) else []
    recommendation = str(parsed.get("recommendation") or "needs_changes")
    if recommendation not in {"approve", "needs_changes", "block"}:
        recommendation = "needs_changes"
    return {
        "summary": str(parsed.get("summary") or "Agent Review completed."),
        "findings": findings,
        "recommendation": recommendation,
    }


def _completion_content(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        return ""
    first = choices[0] if isinstance(choices[0], dict) else {}
    raw_message = first.get("message")
    message = raw_message if isinstance(raw_message, dict) else {}
    content = message.get("content", first.get("text", ""))
    return content if isinstance(content, str) else str(content)


def _agent_review_session_key_hash(task_id: str, timestamp: str) -> str:
    return hashlib.sha256(f"agent-review:v1:{task_id}:{timestamp}".encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _safe_review_value(value: Any, key_hint: str = "") -> Any:
    secret_terms = {"api_key", "key", "secret", "password", "authorization"}
    if isinstance(value, dict):
        safe = {}
        for key, nested in value.items():
            normalized_key = str(key).lower()
            if normalized_key not in TOKEN_EVIDENCE_KEYS and any(term in normalized_key for term in secret_terms):
                continue
            safe[key] = _safe_review_value(nested, str(key))
        return safe
    if isinstance(value, list):
        return [_safe_review_value(item, key_hint) for item in value]
    if isinstance(value, str):
        return SECRET_TEXT_PATTERN.sub("***REDACTED***", value)[:1000]
    return value


def _markdown_breakdown_metadata(description: str) -> dict[str, Any]:
    items: list[str] = []
    for raw_line in description.splitlines():
        line = raw_line.strip()
        if line.startswith("- [ ]") or line.startswith("- [x]"):
            item = line[5:].strip()
        elif line.startswith("- ") or line.startswith("* "):
            item = line[2:].strip()
        elif len(line) > 3 and line[0].isdigit() and line[1:3] == ". ":
            item = line[3:].strip()
        else:
            continue
        if item:
            items.append(item)
    if len(items) < 2:
        return {}
    return {
        "task_breakdown": {
            "source": "markdown_structure",
            "items": items,
            "count": len(items),
            "spend_category": "task_breakdown",
        }
    }


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
        raw["budget_override"] = "budget_override" in raw
        raw["native_budget_acknowledged"] = "native_budget_acknowledged" in raw
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
        normalized_status = "Estimated" if payload.status == "Ready" else payload.status
        if normalized_status in CANONICAL_TASK_STATUSES:
            lifecycle_status = _constrain_direct_lifecycle_status(
                database_path,
                requested_status=normalized_status,
                session_id=payload.session_id,
                metadata=metadata,
            )
            if lifecycle_status is not None:
                return lifecycle_status, metadata
            if normalized_status != "Blocked" and not has_estimate:
                metadata.setdefault("blocked_reason", "Estimate task before launch.")
                metadata.setdefault("requires_manual_estimate", True)
                metadata.setdefault("requested_status", payload.status)
                return "Blocked", metadata
            return normalized_status, metadata
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

    requested_status = "Estimated" if updates["status"] == "Ready" else updates["status"]
    if requested_status not in CANONICAL_TASK_STATUSES:
        updates["status"] = "Blocked"
        metadata.setdefault("blocked_reason", f"Unsupported task status: {requested_status}")
        metadata.setdefault("original_status", requested_status)
        updates["metadata"] = metadata
        return updates

    updates["status"] = requested_status

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

    if requested_status == "Estimated" and (
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
