from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from pydantic import ValidationError

from agile_ai_htb import db
from agile_ai_htb.auth import require_portal_auth
from agile_ai_htb.estimation import EstimatorError, estimate_task
from agile_ai_htb.evidence_reporting import completion_content as _completion_content
from agile_ai_htb.evidence_reporting import safe_evidence as _safe_review_value
from agile_ai_htb.evidence_reporting import token_totals
from agile_ai_htb.llm import LLMClientError, calculate_cost, extract_usage, response_to_dict
from agile_ai_htb.project_context import project_task_metadata, task_project_board_path
from agile_ai_htb.repo_context import build_repo_context_brief
from agile_ai_htb.task_launch import DEFAULT_PROXY_URL, TaskLaunchBlocked, launch_task, refresh_task_from_session
from agile_ai_htb.task_breakdown import (
    TaskBreakdownError,
    breakdown_task_source,
    validate_breakdown_result,
)
from agile_ai_htb.template_context import portal_template_context
from agile_ai_htb.worker_model_allowlist import allowed_worker_model_ids

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).resolve().parents[1] / "templates",
    context_processors=[portal_template_context],
)
CANONICAL_TASK_STATUSES = {"Estimated", "Running", "Review", "Done", "Blocked"}
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
    adapter_id: str | None = None
    remaining_daily_tokens: NonNegativeStrictInt | None = None
    daily_cap_tokens: PositiveStrictInt | None = None


class TaskLaunchRequest(BaseModel):
    adapter_id: str | None = None
    model: str | None = None
    proxy_url: str | None = None
    project_id: str | None = None
    estimate_tokens: PositiveStrictInt | None = None
    budget_override: bool = False
    native_budget_acknowledged: bool = False


class TaskReviewActionRequest(BaseModel):
    action: str = Field(pattern="^(save_prompt|agent_review|mark_done|block)$")
    project_id: str | None = None
    review_prompt: str | None = None
    blocked_reason: str | None = None


@router.post("/tasks")
def create_task(payload: TaskCreateRequest, request: Request) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    status, metadata = _initial_task_status_and_metadata(payload, database_path)
    if status != "Blocked":
        metadata = _with_single_project_default(database_path, metadata)
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
            project_id=payload.project_id,
            estimate_tokens=payload.estimate_tokens,
            budget_override=payload.budget_override,
            native_budget_acknowledged=payload.native_budget_acknowledged,
            budget_since=_current_day_start_iso(request.app.state.settings.timezone),
            runner=runner,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="task not found") from exc
    except TaskLaunchBlocked as exc:
        if wants_html:
            redirect_path = _board_redirect_for_task(exc.task, payload.project_id)
            if exc.task.get("metadata", {}).get("launch_retryable"):
                return RedirectResponse(redirect_path, status_code=303)
            from urllib.parse import quote
            error_msg = "; ".join(exc.reasons) if exc.reasons else "Launch failed."
            return RedirectResponse(f"{redirect_path}?error={quote(error_msg)}", status_code=303)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "task": exc.task,
                "session": exc.task.get("session_id"),
                "launch_guardrails": {"passed": False, "reasons": exc.reasons},
            },
        )
    if wants_html:
        return RedirectResponse(_board_redirect_for_task(result.task, payload.project_id), status_code=303)
    return result.as_response()


@router.post("/tasks/{task_id}/refresh", dependencies=[Depends(require_portal_auth)])
async def refresh_task_endpoint(task_id: str, request: Request):
    try:
        database_path = request.app.state.settings.database_path
        db.mark_stale_worker_runs_interrupted(database_path)
        task = refresh_task_from_session(database_path, task_id)
        if "text/html" in request.headers.get("accept", ""):
            form = await request.form()
            return RedirectResponse(_board_redirect_for_task(task, _form_project_id(form)), status_code=303)
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

            return RedirectResponse(f"{_board_redirect_for_task(task, payload.project_id)}?error={quote(str(exc))}", status_code=303)
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if wants_html:
        return RedirectResponse(_board_redirect_for_task(updated, payload.project_id), status_code=303)
    return updated


@router.post("/estimate", dependencies=[Depends(require_portal_auth)])
async def estimate(payload: EstimateRequest, request: Request) -> dict[str, Any]:
    return await _estimate_and_create_task(
        request,
        payload.description,
        adapter_id=payload.adapter_id,
        remaining_daily_tokens=payload.remaining_daily_tokens,
        daily_cap_tokens=payload.daily_cap_tokens,
    )


async def _estimate_and_create_task(
    request: Request,
    description: str,
    *,
    adapter_id: str | None = None,
    remaining_daily_tokens: int | None = None,
    daily_cap_tokens: int | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    settings = request.app.state.settings
    estimator_model = settings.estimator_model
    try:
        project_root = (extra_metadata or {}).get("project_root_path")
        result, llm_response = await estimate_task(
            description,
            request.app.state.guardrails,
            llm_client=request.app.state.llm_client,
            estimator_model=estimator_model,
            remaining_daily_tokens=remaining_daily_tokens,
            daily_cap_tokens=daily_cap_tokens,
            project_root=project_root,
        )
    except EstimatorError as exc:
        return db.create_task(
            database_path,
            description=description,
            status="Blocked",
            metadata={
                "blocked_reason": "Estimator unavailable or invalid; manual estimate required.",
                "requires_manual_estimate": True,
                "estimation_source": "manual_required",
                "estimator_failure_type": type(exc).__name__,
                **(extra_metadata or {}),
            },
        )

    estimation_session = db.create_session(
        database_path,
        task_description=description,
        model=estimator_model,
        session_key_hash=_estimation_session_key_hash(description),
        guardrail_overrides={},
        status="completed",
    )
    usage = extract_usage(llm_response)
    db.record_token_turn(
        database_path,
        session_id=estimation_session["id"],
        usage_kind="estimation",
        model=estimator_model,
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
        cost=calculate_cost(estimator_model, usage["prompt_tokens"], usage["completion_tokens"])
        or 0.0,
        raw_usage={**usage, "response": response_to_dict(llm_response)},
    )
    recommended_model, model_metadata = _constrained_recommended_model(
        database_path,
        result.recommended_model,
        adapter_id=adapter_id,
        estimate_tokens=result.token_estimate,
        complexity=result.complexity,
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
        **(extra_metadata or {}),
        **model_metadata,
    }
    metadata = _with_single_project_default(database_path, metadata)
    task = db.create_task(
        database_path,
        description=description,
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
    estimate_tokens: int | None = None,
    complexity: str | None = None,
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
    models = allowed_worker_model_ids(adapter)
    metadata = {
        "worker_model_constraint": {
            "state": "constrained_by_allowed_models",
            "adapter_id": adapter["id"],
            "available_models": models,
            "original_model": recommended_model,
        }
    }
    if not models:
        metadata["worker_model_constraint"]["state"] = "no_allowed_models"
        return recommended_model, metadata
    if recommended_model in models:
        metadata["worker_model_constraint"]["selected_model"] = recommended_model
        return recommended_model, metadata
    selected_model = _rank_discovered_worker_model(models, estimate_tokens=estimate_tokens, complexity=complexity)
    reason = "estimator_model_not_allowed"
    if selected_model != models[0]:
        reason = "estimator_model_not_allowed_ranked"
    metadata["worker_model_constraint"].update({"selected_model": selected_model, "reason": reason})
    return str(selected_model), metadata


def _rank_discovered_worker_model(
    models: list[str], *, estimate_tokens: int | None, complexity: str | None
) -> str:
    if not models:
        raise ValueError("models must not be empty")
    normalized_complexity = (complexity or "").strip().lower()
    simple_task = (estimate_tokens is not None and estimate_tokens <= 10_000) or normalized_complexity in {
        "simple",
        "modest",
        "small",
        "low",
    }
    if not simple_task:
        return str(models[0])

    def score(model: str, index: int) -> tuple[int, int]:
        lowered = model.lower()
        if any(term in lowered for term in ("haiku", "mini", "nano", "flash")):
            return (0, index)
        if any(term in lowered for term in ("big-pickle", "opus", "pro", "max")):
            return (20, index)
        return (10, index)

    return min(((str(model), index) for index, model in enumerate(models)), key=lambda item: score(item[0], item[1]))[0]


@router.post("/tasks/estimate-form", dependencies=[Depends(require_portal_auth)])
async def estimate_form(
    request: Request,
    description: str = Form(""),
    markdown_file: UploadFile | None = File(None),
) -> RedirectResponse:
    """HTML form intake: POST plain text or Markdown → estimate → redirect to board."""
    return await _estimate_form_for_project(request, description=description, markdown_file=markdown_file)


@router.post("/projects/{project_id}/tasks/estimate-form", dependencies=[Depends(require_portal_auth)])
async def project_estimate_form(
    project_id: str,
    request: Request,
    description: str = Form(""),
    markdown_file: UploadFile | None = File(None),
) -> RedirectResponse:
    return await _estimate_form_for_project(
        request,
        description=description,
        markdown_file=markdown_file,
        project_id=project_id,
    )


async def _estimate_form_for_project(
    request: Request,
    *,
    description: str,
    markdown_file: UploadFile | None,
    project_id: str | None = None,
) -> RedirectResponse:
    project_metadata: dict[str, Any] = {}
    board_path = "/board"
    if project_id:
        try:
            project = db.get_connected_project(request.app.state.settings.database_path, project_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="connected project not found") from exc
        project_metadata = project_task_metadata(project)
        board_path = f"/projects/{project_id}/board"
    try:
        normalized_description, intake_metadata = await _description_from_intake_form(description, markdown_file)
    except ValueError as exc:
        from urllib.parse import quote

        return RedirectResponse(f"{board_path}?error={quote(str(exc))}", status_code=303)

    intake_metadata = _with_single_project_default(
        request.app.state.settings.database_path,
        {**intake_metadata, **project_metadata},
    )

    if _requires_task_breakdown_review(normalized_description, intake_metadata):
        breakdown = await _create_task_breakdown_review(request, normalized_description, intake_metadata)
        return RedirectResponse(f"/task-breakdowns/{breakdown['id']}/review", status_code=303)

    await _estimate_and_create_task(request, normalized_description, extra_metadata=intake_metadata)
    return RedirectResponse(board_path, status_code=303)


@router.get("/task-breakdowns/{breakdown_id}/review", response_class=HTMLResponse, dependencies=[Depends(require_portal_auth)])
def task_breakdown_review(breakdown_id: str, request: Request) -> HTMLResponse:
    try:
        breakdown = db.get_task_breakdown(request.app.state.settings.database_path, breakdown_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task breakdown not found") from exc
    return templates.TemplateResponse(
        request,
        "task_breakdown_review.html",
        {"active_page": "board", "breakdown": breakdown, "board_path": _breakdown_board_path(breakdown)},
    )


@router.post("/task-breakdowns/{breakdown_id}/accept", dependencies=[Depends(require_portal_auth)])
async def accept_task_breakdown(breakdown_id: str, request: Request) -> RedirectResponse:
    database_path = request.app.state.settings.database_path
    try:
        breakdown = db.get_task_breakdown(database_path, breakdown_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task breakdown not found") from exc
    if breakdown["status"] == "accepted":
        return RedirectResponse(_breakdown_board_path(breakdown), status_code=303)
    if breakdown["status"] == "failed":
        return RedirectResponse(f"/task-breakdowns/{breakdown_id}/review", status_code=303)

    form = await request.form()
    global_contract_summary = str(
        form.get("global_contract_summary") or breakdown.get("global_contract_summary") or ""
    ).strip()
    global_constraints = _textarea_lines(str(form.get("global_constraints") or ""))
    verification = _textarea_lines(str(form.get("verification") or ""))
    accepted_candidates = _accepted_breakdown_candidates(breakdown, form)
    created_task_ids: list[str] = []
    for index, candidate in enumerate(accepted_candidates, start=1):
        description = _breakdown_candidate_description(
            candidate,
            global_contract_summary,
            global_constraints,
            verification,
            source_text=breakdown.get("source_text", ""),
        )
        task = await _estimate_and_create_task(
            request,
            description,
            extra_metadata={
                **breakdown.get("intake_metadata", {}),
                "task_breakdown_id": breakdown["id"],
                "task_breakdown_source_sha256": breakdown["source_sha256"],
                "task_breakdown_decision": breakdown["decision"],
                "task_breakdown_index": index,
                "task_breakdown_count": len(accepted_candidates),
                "task_breakdown_kind": candidate["kind"],
                "task_breakdown_title": candidate["title"],
                "task_breakdown_prompt": candidate["prompt"],
                "task_breakdown_acceptance_criteria": candidate["acceptance_criteria"],
                "task_breakdown_constraints": candidate["constraints"],
                "task_breakdown_global_contract_summary": global_contract_summary,
                "task_breakdown_global_constraints": global_constraints,
                "task_breakdown_verification": verification,
                "task_breakdown_recommended_last": candidate["kind"] == "acceptance_verification",
            },
        )
        created_task_ids.append(task["id"])
    db.update_task_breakdown(
        database_path,
        breakdown_id,
        {
            "status": "accepted",
            "candidates": accepted_candidates,
            "global_contract_summary": global_contract_summary,
            "global_constraints": global_constraints,
            "verification": verification,
            "created_task_ids": created_task_ids,
        },
    )
    return RedirectResponse(_breakdown_board_path(breakdown), status_code=303)


@router.post("/task-breakdowns/{breakdown_id}/retry", dependencies=[Depends(require_portal_auth)])
async def retry_task_breakdown(breakdown_id: str, request: Request) -> RedirectResponse:
    database_path = request.app.state.settings.database_path
    try:
        breakdown = db.get_task_breakdown(database_path, breakdown_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task breakdown not found") from exc
    if breakdown["status"] == "accepted":
        return RedirectResponse(_breakdown_board_path(breakdown), status_code=303)
    updates = await _task_breakdown_agent_updates(
        request,
        breakdown["source_text"],
        breakdown.get("intake_metadata", {}),
        source_sha256=breakdown["source_sha256"],
    )
    db.update_task_breakdown(database_path, breakdown_id, updates)
    return RedirectResponse(f"/task-breakdowns/{breakdown_id}/review", status_code=303)


@router.post("/task-breakdowns/{breakdown_id}/manual", dependencies=[Depends(require_portal_auth)])
async def manual_task_breakdown_candidate(
    breakdown_id: str,
    request: Request,
    title: str = Form(""),
    prompt: str = Form(""),
    acceptance_criteria: str = Form(""),
) -> RedirectResponse:
    database_path = request.app.state.settings.database_path
    try:
        breakdown = db.get_task_breakdown(database_path, breakdown_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task breakdown not found") from exc
    if breakdown["status"] == "accepted":
        return RedirectResponse(_breakdown_board_path(breakdown), status_code=303)
    candidate = {
        "kind": "implementation",
        "title": (title or "Manual task from source").strip(),
        "prompt": (prompt or breakdown["source_text"]).strip(),
        "acceptance_criteria": acceptance_criteria.strip(),
        "constraints": [],
        "human_in_loop": True,
    }
    db.update_task_breakdown(
        database_path,
        breakdown_id,
        {
            "status": "proposed",
            "decision": "single_task",
            "candidates": [candidate],
            "failure_type": None,
            "failure_message": None,
        },
    )
    return RedirectResponse(f"/task-breakdowns/{breakdown_id}/review", status_code=303)


def _requires_task_breakdown_review(description: str, intake_metadata: dict[str, Any]) -> bool:
    if intake_metadata.get("intake_source") in {"markdown_paste", "markdown_upload"}:
        return True
    return len(description.split()) >= 120


async def _create_task_breakdown_review(
    request: Request, description: str, intake_metadata: dict[str, Any]
) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    source_sha256 = hashlib.sha256(description.encode("utf-8")).hexdigest()
    payload = await _task_breakdown_agent_updates(
        request,
        description,
        intake_metadata,
        source_sha256=source_sha256,
    )
    return db.create_task_breakdown(
        database_path,
        source_text=description,
        source_sha256=source_sha256,
        intake_metadata=intake_metadata,
        **payload,
    )


async def _task_breakdown_agent_updates(
    request: Request,
    description: str,
    intake_metadata: dict[str, Any],
    *,
    source_sha256: str,
) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    settings = request.app.state.settings
    model = settings.task_breakdown_model
    repo_context, repo_context_evidence = _build_breakdown_repo_context(intake_metadata)
    try:
        result, response = await breakdown_task_source(
            description,
            llm_client=request.app.state.llm_client,
            task_breakdown_model=model,
            intake_metadata=intake_metadata,
            structure_hints=_markdown_task_items(description),
            repo_context=repo_context,
        )
        session = db.create_session(
            database_path,
            task_description=f"Task breakdown review for {source_sha256[:12]}",
            model=model,
            session_key_hash=_task_breakdown_session_key_hash(source_sha256),
            guardrail_overrides={"spend_category": "task_breakdown"},
            status="completed",
        )
        response_body = response_to_dict(response)
        usage = extract_usage(response_body)
        db.record_token_turn(
            database_path,
            session_id=session["id"],
            usage_kind="task_breakdown",
            model=model,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            cost=calculate_cost(model, usage["prompt_tokens"], usage["completion_tokens"]) or 0.0,
            raw_usage={**usage, "spend_category": "task_breakdown", "usage_source": "control_plane"},
        )
        payload = result.as_dict()
        return {
            "status": "proposed",
            "decision": payload["decision"],
            "model": model,
            "session_id": session["id"],
            "candidates": payload["candidates"],
            "rejected_items": payload["rejected_items"],
            "global_contract_summary": payload["global_contract_summary"],
            "global_constraints": payload["global_constraints"],
            "verification": payload["verification"],
            "non_goals": payload["non_goals"],
            "recommended_sequence": payload["recommended_sequence"],
            "repo_context_evidence": repo_context_evidence or {},
            "confidence": payload["confidence"],
            "rationale": payload["rationale"],
            "failure_type": None,
            "failure_message": None,
        }
    except TaskBreakdownError as exc:
        reason = str(_safe_review_value(str(exc))).strip()
        failure_message = "Task Breakdown Agent failed; retry or create a manual candidate."
        if reason:
            failure_message = f"Task Breakdown Agent failed: {reason}. Retry or create a manual candidate."
        return {
            "status": "failed",
            "decision": "manual_required",
            "model": model,
            "session_id": None,
            "candidates": [],
            "rejected_items": [],
            "global_contract_summary": "",
            "global_constraints": [],
            "verification": [],
            "non_goals": [],
            "recommended_sequence": [],
            "repo_context_evidence": repo_context_evidence or {},
            "confidence": None,
            "rationale": "",
            "failure_type": type(exc).__name__,
            "failure_message": failure_message,
        }


def _build_breakdown_repo_context(intake_metadata: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    project_root = str(intake_metadata.get("project_root_path") or "").strip()
    if not project_root:
        return None, None
    root = Path(project_root).expanduser()
    if not root.is_dir():
        return None, None
    try:
        brief = build_repo_context_brief(root)
    except OSError:
        return None, None
    return brief, _breakdown_repo_context_evidence(brief)


def _breakdown_repo_context_evidence(brief: dict[str, Any]) -> dict[str, Any]:
    documents = [
        str(document.get("path"))
        for document in brief.get("documents", [])
        if isinstance(document, dict) and document.get("path")
    ]
    return {
        "source": "repo_context_brief",
        "project_root": brief.get("project_root"),
        "documents": documents[:10],
        "manifests": list(brief.get("manifests", []))[:10],
        "entrypoints": list(brief.get("entrypoints", []))[:10],
        "test_commands": list(brief.get("test_commands", []))[:10],
        "tracked_files_sample": list(brief.get("tracked_files_sample", []))[:40],
        "text_chars": len(str(brief.get("text") or "")),
    }


def _accepted_breakdown_candidates(breakdown: dict[str, Any], form: Any) -> list[dict[str, Any]]:
    accepted: list[dict[str, Any]] = []
    for index, original in enumerate(breakdown.get("candidates", [])):
        if f"accept_{index}" not in form:
            continue
        title = str(form.get(f"title_{index}") or original.get("title") or "").strip()
        prompt = str(form.get(f"prompt_{index}") or original.get("prompt") or "").strip()
        kind = str(form.get(f"kind_{index}") or original.get("kind") or "implementation").strip()
        if not title or not prompt:
            continue
        accepted.append(
            {
                "kind": kind,
                "title": title,
                "prompt": prompt,
                "acceptance_criteria": str(
                    form.get(f"acceptance_criteria_{index}")
                    or original.get("acceptance_criteria")
                    or ""
                ).strip(),
                "constraints": _textarea_lines(
                    str(form.get(f"constraints_{index}") or "\n".join(original.get("constraints", [])))
                ),
                "human_in_loop": True,
            }
        )
    if not accepted:
        raise HTTPException(status_code=422, detail="Select at least one task candidate to accept.")
    validate_breakdown_result(
        {
            "decision": breakdown.get("decision") if breakdown.get("decision") in {"single_task", "proposed_task_breakdown"} else "proposed_task_breakdown",
            "candidates": accepted,
            "rejected_items": breakdown.get("rejected_items", []),
            "global_contract_summary": breakdown.get("global_contract_summary", ""),
            "global_constraints": breakdown.get("global_constraints", []),
            "verification": breakdown.get("verification", []),
            "non_goals": breakdown.get("non_goals", []),
            "recommended_sequence": breakdown.get("recommended_sequence", []),
            "confidence": breakdown.get("confidence") or 0,
            "rationale": breakdown.get("rationale") or "Operator-edited candidate.",
            "source": "llm",
        }
    )
    return accepted


def _breakdown_candidate_description(
    candidate: dict[str, Any],
    global_contract_summary: str,
    global_constraints: list[str],
    verification: list[str],
    *,
    source_text: str,
) -> str:
    sections = [candidate["title"], "", candidate["prompt"]]
    if global_contract_summary:
        sections.extend(["", "Global contract summary:", global_contract_summary])
    if candidate.get("kind") == "acceptance_verification":
        sections.extend(
            [
                "",
                "Acceptance Verification scope:",
                "Verify the combined artifact against the original source contract. Use the smallest executable proof available and report findings. Do not reimplement the whole source task as one oversized implementation task.",
            ]
        )
        if source_text.strip():
            sections.extend(["", "Original source contract:", source_text.strip()])
    if candidate.get("acceptance_criteria"):
        sections.extend(["", "Acceptance criteria:", candidate["acceptance_criteria"]])
    combined_constraints = [*global_constraints, *candidate.get("constraints", [])]
    if combined_constraints:
        sections.extend(["", "Constraints:", *[f"- {item}" for item in combined_constraints]])
    if verification:
        sections.extend(["", "Verification:", *[f"- {item}" for item in verification]])
    return "\n".join(sections).strip()


def _textarea_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _task_breakdown_session_key_hash(source_sha256: str) -> str:
    return hashlib.sha256(f"task-breakdown:v1:{source_sha256}:{_now_iso()}".encode("utf-8")).hexdigest()


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


def _markdown_task_items(description: str) -> list[str]:
    items: list[str] = []
    for raw_line in description.splitlines():
        line = raw_line.strip()
        if line.startswith("- [ ]") or line.startswith("- [x]"):
            item = line[5:].strip()
        elif line.startswith("* [ ]") or line.startswith("* [x]"):
            item = line[5:].strip()
        elif line.startswith("- ") or line.startswith("* "):
            item = line[2:].strip()
        elif len(line) > 3 and line[0].isdigit() and line[1:3] == ". ":
            item = line[3:].strip()
        else:
            continue
        if item:
            items.append(item)
    return items


def _markdown_source_title(description: str) -> str | None:
    for raw_line in description.splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip() or None
    return None


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
            raw_usage={
                **usage,
                "spend_category": "reporting_summary",
                "usage_source": "control_plane",
                "reporting_kind": "agent_review",
                "response": _safe_review_value(response_body),
            },
        )
        review = _parse_agent_review(_completion_content(response_body))
        review.update(
            {
                "status": "completed",
                "reviewed_at": _now_iso(),
                "review_session_id": review_session["id"],
                "model": settings.control_plane_model,
                "token_totals": _agent_review_token_totals(database_path, review_session["id"]),
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
            "token_totals": _agent_review_token_totals(database_path, review_session["id"]),
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


def _agent_review_session_key_hash(task_id: str, timestamp: str) -> str:
    return hashlib.sha256(f"agent-review:v1:{task_id}:{timestamp}".encode("utf-8")).hexdigest()


def _agent_review_token_totals(database_path: Path | str, session_id: str) -> dict[str, int]:
    try:
        artifact = db.build_session_artifact(database_path, session_id)
    except KeyError:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    return token_totals(artifact)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _current_day_start_iso(timezone: str) -> str:
    if timezone == "local":
        now = datetime.now().astimezone()
    else:
        try:
            now = datetime.now(ZoneInfo(timezone))
        except Exception:
            now = datetime.now(UTC)
    return now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC).isoformat()


def _estimation_session_key_hash(description: str) -> str:
    stable_key = f"estimation:v1:{description}"
    return hashlib.sha256(stable_key.encode("utf-8")).hexdigest()


def _form_project_id(form: Any) -> str | None:
    value = form.get("project_id") if hasattr(form, "get") else None
    return str(value) if value else None


def _project_board_path(project_id: str | None) -> str:
    if project_id:
        return f"/projects/{project_id}/board"
    return "/board"


def _board_redirect_for_task(task: dict[str, Any], project_id: str | None = None) -> str:
    task_board_path = task_project_board_path(task)
    if task_board_path != "/board":
        return task_board_path
    return _project_board_path(project_id)


def _with_single_project_default(database_path: Path | str, metadata: dict[str, Any]) -> dict[str, Any]:
    if metadata.get("connected_project_id"):
        return metadata
    projects = db.list_connected_projects(database_path)
    if len(projects) != 1:
        return metadata
    return {**project_task_metadata(projects[0]), **metadata}


def _breakdown_board_path(breakdown: dict[str, Any]) -> str:
    return task_project_board_path(breakdown.get("intake_metadata", {}))


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
