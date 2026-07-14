from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from foreman_ai_hq import db
from foreman_ai_hq.auth import require_portal_auth
from foreman_ai_hq.evidence_reporting import (
    daily_cap_tokens,
    safe_evidence,
    session_evidence_summary,
    token_component_summary_from_log,
    token_totals,
)
from foreman_ai_hq.guardrails import get_budget_zone

router = APIRouter()
_ACTIVE = {"active", "running"}
_CATEGORIES = (
    "control_plane",
    "task_breakdown",
    "worker_execution",
    "adapter_verification",
    "reporting_summary",
    "other",
)
_COLLECTIONS = {
    "token-log": (50, 100),
    "zone-timeline": (50, 100),
    "worker-timeline": (100, 200),
    "repo-context": (20, 100),
    "alarms": (50, 100),
    "checkpoints": (50, 100),
    "agent-review-findings": (50, 100),
}
_DYNAMIC_COLLECTION = re.compile(r"repo-(documents|manifests)-(0|[1-9]\d*)\Z")
_DYNAMIC_TEXT = re.compile(
    r"(token-raw|worker-detail|repo-text|checkpoint-detail|agent-review-finding)-(0|[1-9]\d*)\Z"
)
_FIXED_TEXT = {
    "task": ("session", "task_description", 20_000),
    "selected-project": ("summary", "selected_project", 1_000),
    "launch-target": ("summary", "launch_target", 4_000),
    "result": ("summary", "result", 4_000),
    "agent-review-summary": ("review", "summary", 4_000),
    "agent-review-error": ("review", "error", 4_000),
}


def build_sessions_context(request: Request) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    config = request.app.state.guardrails
    review_sessions = {
        str(review["review_session_id"]): task.get("id")
        for task in db.list_tasks(database_path)
        if (review := _mapping(_mapping(task.get("metadata")).get("agent_review"))).get("review_session_id")
    }
    rows = []
    for session in reversed(db.list_sessions(database_path)):
        artifact = db.build_session_artifact(database_path, session["id"])
        if session["id"] in review_sessions:
            artifact["session"]["guardrail_overrides"] = {
                **_mapping(artifact["session"].get("guardrail_overrides")),
                "spend_category": "agent_review",
                "task_id": review_sessions[session["id"]],
            }
        totals = token_totals(artifact)
        budget = _mapping(artifact["session"].get("guardrail_overrides")).get("budget")
        budget = _mapping(budget)
        try:
            prior = int(budget.get("daily_used_tokens", 0))
        except (TypeError, ValueError):
            prior = 0
        rows.append(
            {
                "session": artifact["session"],
                "token_totals": totals,
                "current_zone": get_budget_zone(
                    prior + totals["total_tokens"], daily_cap_tokens(budget, config), config
                ),
                "alarms": artifact["alarms"],
                "evidence_summary": session_evidence_summary(artifact),
            }
        )
    return {"active_page": "sessions", "sessions": rows}


def build_session_report_context(request: Request, session_id: str) -> dict[str, Any]:
    database_path = request.app.state.settings.database_path
    try:
        artifact = db.build_session_artifact(database_path, session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc
    artifact = dict(artifact)
    artifact["worker_run_events"] = [
        {**event, "detail": _redact(event.get("detail") or {})}
        for event in artifact.get("worker_run_events", [])
    ]
    review = _related_agent_review(database_path, session_id)
    if review and review.get("_relation") == "session":
        artifact["session"]["guardrail_overrides"] = {
            **_mapping(artifact["session"].get("guardrail_overrides")),
            "spend_category": "agent_review",
            "task_id": review.get("task_id"),
        }
    summary = session_evidence_summary(artifact)
    if review and review.get("_relation") == "session":
        summary = dict(summary)
        summary["selected_project"] = f"Agent Review: {review.get('_task_description') or 'unknown task'}"
        summary["result"] = (
            review.get("error")
            or review.get("summary")
            or review.get("recommendation")
            or review.get("status")
            or summary["result"]
        )
        summary["requires_review"] = bool(review.get("error")) or review.get("status") == "failed"
    return {
        "artifact": artifact,
        "active_page": "sessions",
        "session": artifact["session"],
        "token_totals": token_totals(artifact),
        "token_breakdown": db.session_token_breakdown(database_path, session_id),
        "worker_token_components": token_component_summary_from_log(
            artifact["token_log"], spend_category="worker_execution"
        ),
        "requires_review": bool(summary["requires_review"]),
        "evidence_summary": summary,
        "related_agent_review": review,
        "zone_timeline": artifact["guardrail_snapshots"],
    }


def _related_agent_review(database_path, session_id: str) -> dict[str, Any] | None:
    tasks = list(reversed(db.list_tasks(database_path)))
    for task in tasks:
        if task.get("session_id") != session_id:
            continue
        review = _mapping(_mapping(task.get("metadata")).get("agent_review"))
        if review:
            return {"task_id": task.get("id"), "_task_description": task.get("description"), "_relation": "related", **review, "review_total_tokens": _review_tokens(database_path, review)}
    for task in tasks:
        review = _mapping(_mapping(task.get("metadata")).get("agent_review"))
        if str(review.get("review_session_id") or "") == session_id:
            return {"task_id": task.get("id"), "_task_description": task.get("description"), "_relation": "session", **review, "review_total_tokens": _review_tokens(database_path, review)}
    return None


def _review_tokens(database_path, review: dict[str, Any]) -> int | None:
    totals = _mapping(review.get("token_totals"))
    value = totals.get("total_tokens")
    if not _is_non_negative_int(value):
        return None
    review_session_id = review.get("review_session_id")
    if not review_session_id:
        return value
    try:
        artifact = db.build_session_artifact(database_path, str(review_session_id))
    except KeyError:
        return None
    return value if artifact.get("token_log") else None


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _count(value: Any) -> int:
    return value if _is_non_negative_int(value) else 0


def _nullable_count(value: Any) -> int | None:
    return value if _is_non_negative_int(value) else None


def _cost(value: Any) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _redact(nested)
            for key, nested in value.items()
            if not _sensitive_key(key)
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        return safe_evidence(value, max_length=max(1_000, len(value)))
    return value


def _sensitive_key(key: Any) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")
    parts = set(normalized.split("_"))
    if parts & {
        "auth",
        "authorization",
        "bearer",
        "cookie",
        "credential",
        "credentials",
        "environment",
        "env",
        "header",
        "headers",
        "passwd",
        "password",
        "pat",
        "secret",
    }:
        return True
    if normalized.endswith("_key") or normalized in {"key", "privatekey"}:
        return True
    return normalized.endswith("_token") and not normalized.endswith("_tokens")


def _text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    redacted = _redact(value)
    return redacted if isinstance(redacted, str) else ""


def _string(value: Any, limit: int) -> str:
    return _text(value)[:limit]


def _optional_string(value: Any, limit: int) -> str | None:
    text = _string(value, limit)
    return text or None


def _json_text(value: Any) -> str:
    if value in (None, "", {}, []):
        return ""
    return json.dumps(_redact(value), ensure_ascii=False, indent=2, sort_keys=True)


def _session_href(session_id: str) -> str:
    return f"/sessions/{quote(session_id, safe='')}"


def _api_prefix(session_id: str) -> str:
    return f"/api/sessions/{quote(session_id, safe='')}"


def _bounded(value: Any, limit: int, href: str) -> dict[str, Any]:
    text = _text(value)
    truncated = len(text) > limit
    return {"preview": text[:limit], "truncated": truncated, "full_href": href if truncated else None}


def _page(items: list[Any], offset: int, limit: int, href: str) -> dict[str, Any]:
    total = len(items)
    end = min(total, offset + limit)
    return {
        "items": items[offset:end],
        "pagination": {
            "offset": offset,
            "limit": limit,
            "total": total,
            "has_more": end < total,
            "next_href": f"{href}?offset={end}&limit={limit}" if end < total else None,
        },
    }


def sessions_projection(context: dict[str, Any], offset: int, limit: int) -> dict[str, Any]:
    rows = context.get("sessions") if isinstance(context.get("sessions"), list) else []
    projected = []
    for row in rows:
        row = _mapping(row)
        session = _mapping(row.get("session"))
        summary = _mapping(row.get("evidence_summary"))
        totals = _mapping(row.get("token_totals"))
        session_id = _string(session.get("id"), 128)
        status = _string(session.get("status"), 64)
        projected.append(
            {
                "id": session_id,
                "kind": _string(summary.get("session_kind"), 32),
                "task_preview": _string(session.get("task_description"), 240),
                "model": _string(session.get("model"), 200),
                "status": status,
                "active": status in _ACTIVE,
                "token_totals": {
                    "prompt_tokens": _count(totals.get("prompt_tokens")),
                    "completion_tokens": _count(totals.get("completion_tokens")),
                    "total_tokens": _count(totals.get("total_tokens")),
                },
                "evidence_counts": {
                    "worker_runs": _count(summary.get("worker_runs")),
                    "worker_events": _count(summary.get("worker_events")),
                    "failed_checkpoints": _count(summary.get("failed_checkpoints")),
                },
                "current_zone": _string(row.get("current_zone"), 32),
                "alarm_count": len(row.get("alarms")) if isinstance(row.get("alarms"), list) else 0,
                "report_href": _session_href(session_id),
            }
        )
    total = len(projected)
    selected = projected[offset : offset + limit]
    has_active = any(item["active"] for item in projected)
    return {
        "sessions": selected,
        "pagination": {"offset": offset, "limit": limit, "total": total, "has_more": offset + limit < total},
        "has_active": has_active,
        "poll_after_ms": 5000 if has_active else None,
    }


def _report_sources(context: dict[str, Any]) -> dict[str, Any]:
    artifact = _mapping(context.get("artifact"))
    summary = _mapping(context.get("evidence_summary"))
    review = context.get("related_agent_review")
    return {"artifact": artifact, "summary": summary, "review": _mapping(review) if isinstance(review, dict) else None}


def _token_items(context: dict[str, Any]) -> list[dict[str, Any]]:
    session_id = _string(_mapping(context.get("session")).get("id"), 128)
    items = []
    for index, turn in enumerate(_mapping(context.get("artifact")).get("token_log") or []):
        turn = _mapping(turn)
        items.append(
            {
                "usage_kind": _string(turn.get("usage_kind"), 64),
                "model": _string(turn.get("model"), 200),
                "prompt_tokens": _count(turn.get("prompt_tokens")),
                "completion_tokens": _count(turn.get("completion_tokens")),
                "total_tokens": _count(turn.get("total_tokens")),
                "cost": _cost(turn.get("cost")),
                "raw_usage": _bounded(
                    _json_text(turn.get("raw_usage")), 20_000, f"{_api_prefix(session_id)}/text/token-raw-{index}"
                ),
            }
        )
    return items


def _zone_items(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "zone": _string(item.get("zone"), 64),
            "max_tokens": _nullable_count(_mapping(item.get("decision")).get("max_tokens")),
            "created_at": _optional_string(item.get("created_at"), 64),
        }
        for item in (_mapping(context.get("artifact")).get("guardrail_snapshots") or [])
        if isinstance(item, dict)
    ]


def _worker_items(context: dict[str, Any]) -> list[dict[str, Any]]:
    session_id = _string(_mapping(context.get("session")).get("id"), 128)
    return [
        {
            "created_at": _optional_string(event.get("created_at"), 64),
            "level": _string(event.get("level"), 64),
            "layer": _string(event.get("layer"), 64),
            "kind": _string(event.get("kind"), 64),
            "title": _string(event.get("title"), 200),
            "detail_summary": _string(event.get("detail_summary"), 1_000),
            "detail": _bounded(
                _json_text(event.get("detail")), 20_000, f"{_api_prefix(session_id)}/text/worker-detail-{index}"
            ),
        }
        for index, event in enumerate(_mapping(context.get("artifact")).get("worker_run_events") or [])
        if isinstance(event, dict)
    ]


def _repo_items(context: dict[str, Any]) -> list[dict[str, Any]]:
    session_id = _string(_mapping(context.get("session")).get("id"), 128)
    result = []
    for run_index, run in enumerate(_mapping(context.get("artifact")).get("worker_runs") or []):
        run = _mapping(run)
        brief = _mapping(_mapping(run.get("metadata")).get("repo_context_brief"))
        if not brief:
            continue
        docs = brief.get("documents") if isinstance(brief.get("documents"), list) else []
        manifests = brief.get("manifests") if isinstance(brief.get("manifests"), list) else []
        prefix = _api_prefix(session_id)
        result.append(
            {
                "worker_run_id": _string(run.get("id"), 128),
                "documents": _page(
                    [{"path": _string(_mapping(doc).get("path"), 1_000)} for doc in docs],
                    0, 50, f"{prefix}/evidence/repo-documents-{run_index}",
                ),
                "manifests": _page(
                    [_string(item, 1_000) for item in manifests],
                    0, 50, f"{prefix}/evidence/repo-manifests-{run_index}",
                ),
                "text": _bounded(brief.get("text"), 40_000, f"{prefix}/text/repo-text-{run_index}"),
            }
        )
    return result


def _alarm_items(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": _string(item.get("id"), 128),
            "type": _string(item.get("type"), 200),
            "severity": _string(item.get("severity"), 64),
            "recommended_action": _string(item.get("recommended_action"), 2_000),
            "created_at": _optional_string(item.get("created_at"), 64),
        }
        for item in (_mapping(context.get("artifact")).get("alarms") or [])
        if isinstance(item, dict)
    ]


def _checkpoint_items(context: dict[str, Any]) -> list[dict[str, Any]]:
    session_id = _string(_mapping(context.get("session")).get("id"), 128)
    return [
        {
            "name": _string(item.get("name"), 200),
            "passed": item.get("passed") if isinstance(item.get("passed"), bool) else False,
            "details": _bounded(
                _json_text(item.get("details")), 20_000, f"{_api_prefix(session_id)}/text/checkpoint-detail-{index}"
            ),
        }
        for index, item in enumerate(_mapping(context.get("artifact")).get("checkpoint_results") or [])
        if isinstance(item, dict)
    ]


def _finding_text(item: Any) -> str:
    return item if isinstance(item, str) else _json_text(item)


def _finding_items(context: dict[str, Any]) -> list[dict[str, Any]]:
    review = _mapping(context.get("related_agent_review"))
    findings = review.get("findings") if isinstance(review.get("findings"), list) else []
    session_id = _string(_mapping(context.get("session")).get("id"), 128)
    return [
        _bounded(_finding_text(item), 4_000, f"{_api_prefix(session_id)}/text/agent-review-finding-{index}")
        for index, item in enumerate(findings)
    ]


def _collection_items(context: dict[str, Any], collection_id: str) -> list[Any]:
    fixed = {
        "token-log": _token_items,
        "zone-timeline": _zone_items,
        "worker-timeline": _worker_items,
        "repo-context": _repo_items,
        "alarms": _alarm_items,
        "checkpoints": _checkpoint_items,
        "agent-review-findings": _finding_items,
    }
    if collection_id in fixed:
        return fixed[collection_id](context)
    match = _DYNAMIC_COLLECTION.fullmatch(collection_id)
    if not match:
        raise HTTPException(status_code=404, detail="evidence collection not found")
    kind, raw_index = match.groups()
    runs = _mapping(context.get("artifact")).get("worker_runs") or []
    index = int(raw_index)
    if index >= len(runs) or not isinstance(runs[index], dict):
        raise HTTPException(status_code=404, detail="evidence collection not found")
    brief = _mapping(_mapping(runs[index].get("metadata")).get("repo_context_brief"))
    values = brief.get(kind)
    if not isinstance(values, list):
        values = []
    if kind == "documents":
        return [{"path": _string(_mapping(item).get("path"), 1_000)} for item in values]
    return [_string(item, 1_000) for item in values]


def _freshness(context: dict[str, Any]) -> dict[str, Any]:
    if isinstance(context.get("freshness"), dict):
        return context["freshness"]
    artifact = _mapping(context.get("artifact"))
    session = _mapping(context.get("session"))
    runs = artifact.get("worker_runs") if isinstance(artifact.get("worker_runs"), list) else []
    markers = {
        "session": [_text(session.get("id")), _text(session.get("status")), _text(session.get("started_at"))],
        "token": [[_text(item.get("created_at")), index] for index, item in enumerate(artifact.get("token_log") or []) if isinstance(item, dict)],
        "snapshot": [[_text(item.get("created_at")), index] for index, item in enumerate(artifact.get("guardrail_snapshots") or []) if isinstance(item, dict)],
        "alarm": [[_text(item.get("id")), _text(item.get("created_at"))] for item in artifact.get("alarms") or [] if isinstance(item, dict)],
        "checkpoint": [[_text(item.get("created_at")), index] for index, item in enumerate(artifact.get("checkpoint_results") or []) if isinstance(item, dict)],
        "runs": [[_text(run.get(key)) if key != "returncode" else run.get(key) for key in ("id", "status", "started_at", "completed_at", "returncode", "error_type", "error_message")] for run in runs if isinstance(run, dict)],
        "events": [[_text(item.get("created_at")), item.get("id")] for item in artifact.get("worker_run_events") or [] if isinstance(item, dict)],
    }
    version = hashlib.sha256(json.dumps(markers, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
    timestamps = [_optional_string(session.get("started_at"), 64)]
    for name in ("token_log", "guardrail_snapshots", "alarms", "checkpoint_results", "worker_runs", "worker_run_events"):
        for item in artifact.get(name) or []:
            if isinstance(item, dict):
                timestamps.extend(_optional_string(item.get(key), 64) for key in ("created_at", "completed_at"))
    timestamps = [item for item in timestamps if item]
    status = _string(session.get("status"), 64)
    return {
        "session_id": _string(session.get("id"), 128),
        "status": status,
        "active": status in _ACTIVE,
        "version": version,
        "last_evidence_at": max(timestamps) if timestamps else None,
    }


def build_session_freshness(database_path, session_id: str) -> dict[str, Any]:
    """Read only append/status revision markers in one transaction."""
    with db.connect(database_path) as conn:
        session = conn.execute(
            "select id, status, started_at from sessions where id = ?", (session_id,)
        ).fetchone()
        if session is None:
            raise HTTPException(status_code=404, detail="session not found")
        tokens = conn.execute(
            "select created_at from token_turns where session_id = ? order by id", (session_id,)
        ).fetchall()
        snapshots = conn.execute(
            "select created_at from guardrail_snapshots where session_id = ? order by id", (session_id,)
        ).fetchall()
        alarms = conn.execute(
            "select id, created_at from alarms where session_id = ? order by created_at, id", (session_id,)
        ).fetchall()
        checkpoints = conn.execute(
            "select created_at from checkpoint_results where session_id = ? order by id", (session_id,)
        ).fetchall()
        runs = conn.execute(
            """select id, status, started_at, completed_at, returncode, error_type,
                      error_message, created_at
               from worker_runs where session_id = ? order by created_at, id""",
            (session_id,),
        ).fetchall()
        events = conn.execute(
            "select id, created_at from worker_run_events where session_id = ? order by created_at, id",
            (session_id,),
        ).fetchall()
    markers = {
        "session": [_text(session["id"]), _text(session["status"]), _text(session["started_at"])],
        "token": [[_text(row["created_at"]), index] for index, row in enumerate(tokens)],
        "snapshot": [[_text(row["created_at"]), index] for index, row in enumerate(snapshots)],
        "alarm": [[_text(row["id"]), _text(row["created_at"])] for row in alarms],
        "checkpoint": [[_text(row["created_at"]), index] for index, row in enumerate(checkpoints)],
        "runs": [
            [
                _text(row[key]) if key != "returncode" else row[key]
                for key in ("id", "status", "started_at", "completed_at", "returncode", "error_type", "error_message")
            ]
            for row in runs
        ],
        "events": [[_text(row["created_at"]), row["id"]] for row in events],
    }
    version = hashlib.sha256(
        json.dumps(markers, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    timestamps = [_optional_string(session["started_at"], 64)]
    timestamps += [
        _optional_string(row["created_at"], 64)
        for rows in (tokens, snapshots, alarms, checkpoints, events)
        for row in rows
    ]
    timestamps += [
        _optional_string(row[key], 64)
        for row in runs
        for key in ("created_at", "completed_at")
    ]
    clean_timestamps = [item for item in timestamps if item]
    status_value = _string(session["status"], 64)
    return {
        "session_id": _string(session["id"], 128),
        "status": status_value,
        "active": status_value in _ACTIVE,
        "version": version,
        "last_evidence_at": max(clean_timestamps) if clean_timestamps else None,
    }


def report_projection(context: dict[str, Any]) -> dict[str, Any]:
    session = _mapping(context.get("session"))
    summary = _mapping(context.get("evidence_summary"))
    totals = _mapping(context.get("token_totals"))
    breakdown = _mapping(context.get("token_breakdown"))
    categories = _mapping(breakdown.get("by_category"))
    components = _mapping(context.get("worker_token_components"))
    session_id = _string(session.get("id"), 128)
    prefix = _api_prefix(session_id)
    review = context.get("related_agent_review")
    review_projection = None
    if isinstance(review, dict):
        review_id = _optional_string(review.get("review_session_id"), 128)
        review_projection = {
            "status": _optional_string(review.get("status"), 200),
            "recommendation": _optional_string(review.get("recommendation"), 200),
            "summary": None if not _text(review.get("summary")) else _bounded(review.get("summary"), 4_000, f"{prefix}/text/agent-review-summary"),
            "model": _optional_string(review.get("model"), 200),
            "reviewed_at": _optional_string(review.get("reviewed_at"), 64),
            "review_session_id": review_id,
            "review_session_href": _session_href(review_id) if review_id and review.get("_relation") != "session" else None,
            "review_total_tokens": _nullable_count(review.get("review_total_tokens")),
            "error": None if not _text(review.get("error")) else _bounded(review.get("error"), 4_000, f"{prefix}/text/agent-review-error"),
            "findings": _page(_finding_items(context), 0, 50, f"{prefix}/evidence/agent-review-findings"),
        }
    return {
        "session": {
            "id": session_id,
            "kind": _string(summary.get("session_kind"), 32),
            "task": _bounded(session.get("task_description"), 20_000, f"{prefix}/text/task"),
            "model": _string(session.get("model"), 200),
            "status": _string(session.get("status"), 64),
            "started_at": _optional_string(session.get("started_at"), 64),
            "active": _string(session.get("status"), 64) in _ACTIVE,
        },
        "summary": {
            "selected_project": _bounded(summary.get("selected_project"), 1_000, f"{prefix}/text/selected-project"),
            "launch_target": _bounded(summary.get("launch_target"), 4_000, f"{prefix}/text/launch-target"),
            "adapter_id": _string(summary.get("adapter_id"), 200),
            "worker_model": _string(summary.get("worker_model"), 200),
            "tracking_mode": _string(summary.get("tracking_mode"), 64),
            "status": _string(summary.get("status"), 64),
            "result": _bounded(summary.get("result"), 4_000, f"{prefix}/text/result"),
            "requires_review": summary.get("requires_review") if isinstance(summary.get("requires_review"), bool) else False,
            "missing_labels": [_string(item, 500) for item in (summary.get("missing_labels") or [])[:20] if isinstance(item, str)],
            "evidence_counts": {key: _count(summary.get(key)) for key in ("alarms", "checkpoints", "failed_checkpoints", "worker_runs", "worker_events", "error_events")},
        },
        "tokens": {
            "provider_totals": {key: _count(totals.get(key)) for key in ("prompt_tokens", "completion_tokens", "total_tokens")},
            "normalized": {"total_tokens": _count(breakdown.get("total_tokens")), "by_category": {key: _count(categories.get(key)) for key in _CATEGORIES}},
            "worker_components": {
                "available": components.get("available") if isinstance(components.get("available"), bool) else False,
                "items": [{"key": _string(_mapping(item).get("key"), 64), "label": _string(_mapping(item).get("label"), 200), "value": _count(_mapping(item).get("value"))} for item in (components.get("items") or [])[:20] if isinstance(item, dict)],
                "cost": _cost(components.get("cost")),
                "turn_count": _count(components.get("turn_count")),
            },
            "log": _page(_token_items(context), 0, 50, f"{prefix}/evidence/token-log"),
        },
        "zone_timeline": _page(_zone_items(context), 0, 50, f"{prefix}/evidence/zone-timeline"),
        "worker_timeline": _page(_worker_items(context), 0, 100, f"{prefix}/evidence/worker-timeline"),
        "repo_context_briefs": _page(_repo_items(context), 0, 20, f"{prefix}/evidence/repo-context"),
        "alarms": _page(_alarm_items(context), 0, 50, f"{prefix}/evidence/alarms"),
        "checkpoints": _page(_checkpoint_items(context), 0, 50, f"{prefix}/evidence/checkpoints"),
        "related_agent_review": review_projection,
        "freshness": _freshness(context),
        "links": {"sessions_href": "/sessions", "self_href": _session_href(session_id)},
    }


def _full_text(context: dict[str, Any], text_id: str) -> str:
    sources = _report_sources(context)
    artifact = sources["artifact"]
    summary = sources["summary"]
    review = sources["review"] or {}
    if text_id in _FIXED_TEXT:
        source, key, limit = _FIXED_TEXT[text_id]
        container = {"session": _mapping(context.get("session")), "summary": summary, "review": review}[source]
        value = _text(container.get(key))
    else:
        match = _DYNAMIC_TEXT.fullmatch(text_id)
        if not match:
            raise HTTPException(status_code=404, detail="report text not found")
        kind, raw_index = match.groups()
        index = int(raw_index)
        if kind == "token-raw":
            values, limit = artifact.get("token_log") or [], 20_000
            value = _json_text(_mapping(values[index]).get("raw_usage")) if index < len(values) else ""
        elif kind == "worker-detail":
            values, limit = artifact.get("worker_run_events") or [], 20_000
            value = _json_text(_mapping(values[index]).get("detail")) if index < len(values) else ""
        elif kind == "repo-text":
            values, limit = artifact.get("worker_runs") or [], 40_000
            value = _text(_mapping(_mapping(_mapping(values[index]).get("metadata")).get("repo_context_brief")).get("text")) if index < len(values) else ""
        elif kind == "checkpoint-detail":
            values, limit = artifact.get("checkpoint_results") or [], 20_000
            value = _json_text(_mapping(values[index]).get("details")) if index < len(values) else ""
        else:
            values, limit = review.get("findings") if isinstance(review.get("findings"), list) else [], 4_000
            value = _finding_text(values[index]) if index < len(values) else ""
    if len(value) <= limit:
        raise HTTPException(status_code=404, detail="report text not found")
    return value


@router.get("/api/sessions", dependencies=[Depends(require_portal_auth)])
def api_sessions(request: Request, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    return sessions_projection(build_sessions_context(request), offset, limit)


@router.get("/api/sessions/{session_id}/report", dependencies=[Depends(require_portal_auth)])
def api_session_report(session_id: str, request: Request):
    return report_projection(build_session_report_context(request, session_id))


@router.get("/api/sessions/{session_id}/evidence/{collection_id}", dependencies=[Depends(require_portal_auth)])
def api_session_evidence(session_id: str, collection_id: str, request: Request, offset: int = Query(0, ge=0), limit: int | None = Query(None, ge=1)):
    context = build_session_report_context(request, session_id)
    dynamic = _DYNAMIC_COLLECTION.fullmatch(collection_id)
    if collection_id in _COLLECTIONS:
        default, maximum = _COLLECTIONS[collection_id]
    elif dynamic:
        default, maximum = 50, 100
    else:
        raise HTTPException(status_code=404, detail="evidence collection not found")
    actual_limit = default if limit is None else limit
    if actual_limit > maximum:
        raise HTTPException(status_code=422, detail=f"limit must be at most {maximum}")
    items = _collection_items(context, collection_id)
    return _page(items, offset, actual_limit, f"{_api_prefix(session_id)}/evidence/{collection_id}")


@router.get("/api/sessions/{session_id}/text/{text_id}", dependencies=[Depends(require_portal_auth)])
def api_session_text(session_id: str, text_id: str, request: Request):
    text = _full_text(build_session_report_context(request, session_id), text_id)
    return PlainTextResponse(text, headers={"Cache-Control": "no-store"})


@router.get("/api/sessions/{session_id}/freshness", dependencies=[Depends(require_portal_auth)])
def api_session_freshness(session_id: str, request: Request):
    return build_session_freshness(request.app.state.settings.database_path, session_id)
