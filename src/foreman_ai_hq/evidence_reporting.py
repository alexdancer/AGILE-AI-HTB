from __future__ import annotations

import json
import re
from typing import Any

from foreman_ai_hq.native_cli_diagnostics import redact_native_cli_text
from foreman_ai_hq.native_usage import token_usage_components

TOKEN_EVIDENCE_KEYS = {"prompt_tokens", "completion_tokens", "total_tokens"}
TOKEN_EVIDENCE_CONTAINERS = {"token_log"}
SECRET_TEXT_PATTERN = re.compile(
    r"((?<!\w)sk[-_][A-Za-z0-9_.-]+|Bearer\s+[A-Za-z0-9_.-]+|password\s*[:=]\s*\S+)",
    re.IGNORECASE,
)


def safe_evidence(value: Any, key_hint: str = "", *, max_length: int = 1000) -> Any:
    secret_terms = {"api_key", "key", "secret", "password", "authorization"}
    if isinstance(value, dict):
        safe = {}
        for key, nested in value.items():
            normalized_key = str(key).lower()
            # Token accounting fields are evidence, not credentials, despite containing "token".
            keeps_token_evidence = normalized_key in TOKEN_EVIDENCE_KEYS or normalized_key in TOKEN_EVIDENCE_CONTAINERS
            if not keeps_token_evidence and (
                any(term in normalized_key for term in secret_terms) or "token" in normalized_key
            ):
                continue
            safe[key] = safe_evidence(nested, str(key), max_length=max_length)
        return safe
    if isinstance(value, list):
        return [safe_evidence(item, key_hint, max_length=max_length) for item in value]
    if isinstance(value, str):
        redacted = redact_native_cli_text(SECRET_TEXT_PATTERN.sub("***REDACTED***", value))
        if redacted != value or value.startswith("sk_"):
            return "***REDACTED***" if redacted == value else redacted[:max_length]
        return value[:max_length]
    return value


def token_totals(artifact: dict[str, Any]) -> dict[str, int]:
    return token_totals_from_log(artifact.get("token_log") or [])


def token_totals_from_log(token_log: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "prompt_tokens": sum(int(turn.get("prompt_tokens", 0)) for turn in token_log),
        "completion_tokens": sum(int(turn.get("completion_tokens", 0)) for turn in token_log),
        "total_tokens": sum(int(turn.get("total_tokens", 0)) for turn in token_log),
    }


def token_component_summary_from_log(
    token_log: list[dict[str, Any]], *, spend_category: str | None = None
) -> dict[str, Any]:
    labels = {
        "normalized_actual": "normalized actual/task budget",
        "provider_raw_total": "provider raw total/evidence",
        "fresh_input": "fresh input/new prompt text",
        "cache_read": "cache read/reused context",
        "cache_write": "cache write/create",
        "output": "output",
        "reasoning": "reasoning",
        "unclassified": "unclassified/provider-total-only",
    }
    totals = dict.fromkeys(labels, 0)
    cost = 0.0
    saw_cost = False
    matched = 0
    for turn in token_log:
        raw_usage = turn.get("raw_usage") or {}
        if spend_category is not None and _turn_spend_category(turn) != spend_category:
            continue
        matched += 1
        components = token_usage_components(
            raw_usage,
            prompt_tokens=turn.get("prompt_tokens"),
            completion_tokens=turn.get("completion_tokens"),
            total_tokens=turn.get("total_tokens"),
            cost=turn.get("cost"),
        )
        for key in totals:
            if components.get(key) is not None:
                totals[key] += int(components[key])
        if components.get("cost") not in (None, 0):
            saw_cost = True
            cost += float(components["cost"])
    items = [{"key": key, "label": labels[key], "value": value} for key, value in totals.items() if value]
    return {"available": bool(items or saw_cost), "items": items, "cost": cost if saw_cost else None, "turn_count": matched}


def _turn_spend_category(turn: dict[str, Any]) -> str:
    raw_usage = turn.get("raw_usage") or {}
    category = raw_usage.get("spend_category")
    if category == "agent_review":
        return "reporting_summary"
    if category:
        return str(category)
    usage_kind = str(turn.get("usage_kind") or "")
    if usage_kind == "task_breakdown":
        return "task_breakdown"
    if usage_kind == "estimation":
        return "control_plane"
    if usage_kind in {"worker", "task_execution"}:
        return "worker_execution"
    if usage_kind == "adapter_verification":
        return "adapter_verification"
    if usage_kind in {"reporting", "summary"}:
        return "reporting_summary"
    return "other"


def daily_cap_tokens(budget: dict[str, Any], config: Any) -> int | None:
    if "daily_cap_tokens" in budget:
        return int(budget["daily_cap_tokens"])
    if config.daily_cap.enabled:
        return config.daily_cap.tokens
    return None


def session_evidence_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    session = artifact.get("session") or {}
    guardrail_overrides = session.get("guardrail_overrides") or {}
    # Agent Review sessions have no Worker Run, so derive their labels from control-plane metadata.
    is_agent_review = guardrail_overrides.get("spend_category") == "agent_review" or str(
        session.get("task_description") or ""
    ).startswith("Agent review for task ")
    checkpoint_results = artifact.get("checkpoint_results") or []
    worker_events = artifact.get("worker_run_events") or []
    worker_runs = artifact.get("worker_runs") or []
    latest_run = worker_runs[-1] if worker_runs else {}
    command_plan = latest_run.get("command_plan") or {}
    command = command_plan.get("command") or []
    if isinstance(command, list):
        launch_target = " ".join(str(part) for part in command) or "missing launch target"
    else:
        launch_target = str(command or "missing launch target")
    metadata = latest_run.get("metadata") or {}
    project_label = (
        metadata.get("connected_project_name")
        or metadata.get("project_name")
        or metadata.get("project_root")
        or metadata.get("workdir")
        or "missing project evidence"
    )
    if is_agent_review:
        launch_target = "control-plane Agent Review"
        task_id = guardrail_overrides.get("task_id")
        project_label = f"Agent Review for task {task_id}" if task_id else "Agent Review"
    tokens = token_totals(artifact)
    agent_review_result = agent_review_result_from_token_log(artifact.get("token_log") or []) if is_agent_review else {}
    failed_checkpoints = [checkpoint for checkpoint in checkpoint_results if not checkpoint.get("passed")]
    error_events = [event for event in worker_events if event.get("level") == "error"]
    missing_labels = []
    if not worker_runs and not is_agent_review:
        missing_labels.append("missing Worker Run evidence")
    if not artifact.get("token_log"):
        missing_labels.append("missing Agent Review token usage" if is_agent_review else "missing authoritative token usage")
    if not artifact.get("alarms") and not failed_checkpoints and not error_events:
        missing_labels.append("no review blockers recorded")
    return {
        "session_kind": "Agent Review" if is_agent_review else "Worker Session",
        "task": session.get("task_description", "missing task evidence"),
        "selected_project": project_label,
        "launch_target": launch_target,
        "adapter_id": "Control Plane" if is_agent_review else latest_run.get("adapter_id") or "missing Worker Adapter evidence",
        "worker_model": latest_run.get("model") or session.get("model") or "missing Worker model evidence",
        "tracking_mode": "reporting_summary" if is_agent_review else latest_run.get("tracking_mode") or "missing tracking-mode evidence",
        "status": latest_run.get("status") or session.get("status") or "missing status evidence",
        "result": agent_review_result.get("display")
        or latest_run.get("error_message")
        or latest_run.get("error_type")
        or latest_run.get("status")
        or session.get("status")
        or "missing result evidence",
        "review_recommendation": agent_review_result.get("recommendation"),
        "review_summary": agent_review_result.get("summary"),
        "token_totals": tokens,
        "missing_labels": missing_labels,
        "alarms": len(artifact.get("alarms") or []),
        "checkpoints": len(checkpoint_results),
        "failed_checkpoints": len(failed_checkpoints),
        "worker_runs": len(worker_runs),
        "worker_events": len(worker_events),
        "error_events": len(error_events),
        "requires_review": bool(artifact.get("alarms")) or bool(failed_checkpoints) or bool(error_events),
    }


def agent_review_result_from_token_log(token_log: list[dict[str, Any]]) -> dict[str, str]:
    for turn in reversed(token_log):
        raw_usage = turn.get("raw_usage") if isinstance(turn, dict) else None
        if not isinstance(raw_usage, dict):
            continue
        if raw_usage.get("reporting_kind") != "agent_review" and raw_usage.get("spend_category") != "agent_review":
            continue
        response = raw_usage.get("response")
        if not isinstance(response, dict):
            continue
        content = completion_content(response)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"summary": content.strip()}
        if not isinstance(parsed, dict):
            parsed = {"summary": str(parsed)}
        recommendation = str(parsed.get("recommendation") or "needs_changes")
        summary = str(parsed.get("summary") or "Agent Review completed.")
        return {"recommendation": recommendation, "summary": summary, "display": f"{recommendation} · {summary}"}
    return {}


def completion_content(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    first = choices[0] if choices and isinstance(choices[0], dict) else {}
    raw_message = first.get("message")
    message = raw_message if isinstance(raw_message, dict) else {}
    content = message.get("content", first.get("text", ""))
    return content if isinstance(content, str) else str(content)
