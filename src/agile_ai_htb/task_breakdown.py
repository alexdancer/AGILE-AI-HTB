from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from agile_ai_htb.llm import response_to_dict
from agile_ai_htb.task_slicing_policy import (
    DEFAULT_TASK_BREAKDOWN_EXECUTION_MODE,
    TASK_BREAKDOWN_EXECUTION_MODES,
    TASK_BREAKDOWN_OUTPUT_SCHEMA,
    TASK_SLICING_POLICY,
)

TASK_BREAKDOWN_CANDIDATE_KINDS = {"implementation", "acceptance_verification"}
TASK_BREAKDOWN_MAX_TOKENS = 16_384
TASK_BREAKDOWN_TIMEOUT_SECONDS = 120
SECRET_TEXT_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_.-]+|sk_[A-Za-z0-9_.-]+|Bearer\s+[A-Za-z0-9_.-]+|(?i:password|token|secret|api[_-]?key)\s*[:=]\s*\S+)"
)


class TaskBreakdownError(Exception):
    """Base class for Task Breakdown Agent failures that require review recovery."""


class TaskBreakdownUnavailableError(TaskBreakdownError):
    """Raised when the Task Breakdown Agent LLM call fails."""


class TaskBreakdownValidationError(TaskBreakdownError):
    """Raised when Task Breakdown Agent output is not valid structured JSON."""


@dataclass(frozen=True)
class BreakdownCandidate:
    kind: str
    title: str
    objective: str
    prompt: str
    acceptance_criteria: str
    constraints: list[str]
    proof: str
    why_this_task_exists: str
    why_not_smaller: str
    why_not_larger: str
    dependencies: list[str]
    likely_entry_points: list[str]
    execution_mode: str = DEFAULT_TASK_BREAKDOWN_EXECUTION_MODE
    hitl_reason: str = ""
    human_in_loop: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "title": self.title,
            "objective": self.objective,
            "prompt": self.prompt,
            "acceptance_criteria": self.acceptance_criteria,
            "constraints": self.constraints,
            "proof": self.proof,
            "why_this_task_exists": self.why_this_task_exists,
            "why_not_smaller": self.why_not_smaller,
            "why_not_larger": self.why_not_larger,
            "dependencies": self.dependencies,
            "likely_entry_points": self.likely_entry_points,
            "execution_mode": self.execution_mode,
            "hitl_reason": self.hitl_reason,
            "human_in_loop": self.human_in_loop,
        }


@dataclass(frozen=True)
class RejectedBreakdownItem:
    text: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"text": self.text, "reason": self.reason}


@dataclass(frozen=True)
class TaskBreakdownResult:
    decision: str
    candidates: list[BreakdownCandidate]
    rejected_items: list[RejectedBreakdownItem]
    global_contract_summary: str
    global_constraints: list[str]
    verification: list[str]
    non_goals: list[str]
    recommended_sequence: list[str]
    confidence: float
    rationale: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "rejected_items": [item.as_dict() for item in self.rejected_items],
            "global_contract_summary": self.global_contract_summary,
            "global_constraints": self.global_constraints,
            "verification": self.verification,
            "non_goals": self.non_goals,
            "recommended_sequence": self.recommended_sequence,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "source": self.source,
        }


async def breakdown_task_source(
    source_text: str,
    *,
    llm_client: Any,
    task_breakdown_model: str,
    intake_metadata: dict[str, Any] | None = None,
    structure_hints: list[str] | None = None,
    repo_context: dict[str, Any] | None = None,
    timeout_seconds: int = TASK_BREAKDOWN_TIMEOUT_SECONDS,
) -> tuple[TaskBreakdownResult, Any]:
    user_payload: dict[str, Any] = {
        "source_text": source_text,
        "intake_metadata": intake_metadata or {},
        "structure_hints": structure_hints or [],
    }
    if repo_context:
        user_payload["repo_context"] = repo_context
    request = {
        "model": task_breakdown_model,
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {
                "role": "user",
                "content": json.dumps(user_payload, sort_keys=True),
            },
        ],
        "temperature": 0,
        "max_tokens": TASK_BREAKDOWN_MAX_TOKENS,
        "timeout_seconds": timeout_seconds,
        "response_format": {"type": "json_object"},
    }
    try:
        response = await llm_client.acompletion(request)
    except Exception as exc:  # pragma: no cover - exercised through route tests
        raise TaskBreakdownUnavailableError(
            _provider_failure_message(
                exc,
                model=task_breakdown_model,
                source_text=source_text,
                timeout_seconds=timeout_seconds,
            )
        ) from exc
    return _parse_response(response), response


def _system_prompt() -> str:
    return "\n\n".join(
        [
            "You are the AGILE-AI-HTB Task Breakdown Agent. Classify Markdown or oversized coding-task input into independently grabbable vertical-slice task candidates for the AGILE Board.",
            TASK_SLICING_POLICY,
            TASK_BREAKDOWN_OUTPUT_SCHEMA,
            (
                "Classify every candidate kind as either 'implementation' or 'acceptance_verification'. "
                "For multi-slice breakdowns that produce one integrated artifact (CLI, app, API, demo, report, or similar), "
                "include one acceptance_verification candidate recommended last. That candidate must verify the combined artifact "
                "against the original source contract using the smallest executable proof available; it must not ask the Worker to "
                "reimplement the whole source task as one oversized implementation task. Write one concise global_contract_summary "
                "describing what all accepted slices must collectively satisfy."
            ),
        ]
    )


def _provider_failure_message(
    exc: Exception,
    *,
    model: str,
    source_text: str,
    timeout_seconds: int,
) -> str:
    reason = _safe_failure_detail(str(exc), source_text=source_text)
    context = (
        f"model={model}; source_chars={len(source_text)}; "
        f"max_output_tokens={TASK_BREAKDOWN_MAX_TOKENS}; timeout_seconds={timeout_seconds}"
    )
    if _looks_like_timeout(exc, reason):
        return f"provider timeout ({context}); {reason}"
    return f"provider rejection or transport failure ({context}); {reason}"


def _safe_failure_detail(detail: str, *, source_text: str) -> str:
    safe = SECRET_TEXT_PATTERN.sub("[REDACTED]", detail)
    for variant in _source_text_redaction_variants(source_text):
        safe = safe.replace(variant, "[REDACTED_SOURCE_TEXT]")
    safe = " ".join(safe.split())
    return safe[:500] or "no provider detail returned"


def _source_text_redaction_variants(source_text: str) -> list[str]:
    if not source_text:
        return []

    variants: list[str] = []
    for value in [source_text, json.dumps(source_text)[1:-1], " ".join(source_text.split())]:
        if value and value not in variants:
            variants.append(value)

    for line in source_text.splitlines():
        stripped = line.strip()
        if len(stripped) < 12:
            continue
        for value in [stripped, json.dumps(stripped)[1:-1], " ".join(stripped.split())]:
            if value and value not in variants:
                variants.append(value)

    variants.sort(key=len, reverse=True)
    return variants


def _looks_like_timeout(exc: Exception, detail: str) -> bool:
    return isinstance(exc, TimeoutError) or "timeout" in detail.lower() or "timed out" in detail.lower()


def _parse_response(response: Any) -> TaskBreakdownResult:
    try:
        data = json.loads(_task_breakdown_json_text(_response_content(response)))
    except Exception as exc:
        raise TaskBreakdownValidationError("task breakdown returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise TaskBreakdownValidationError("task breakdown JSON must be an object")
    return validate_breakdown_result(data)


def _task_breakdown_json_text(content: str) -> str:
    text = content.strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if len(lines) < 3:
        raise TaskBreakdownValidationError("task breakdown returned invalid JSON")
    opening = lines[0].strip()
    language = opening[3:].strip().lower()
    if language not in {"", "json"}:
        raise TaskBreakdownValidationError("task breakdown returned invalid JSON")
    if lines[-1].strip() != "```":
        raise TaskBreakdownValidationError("task breakdown returned invalid JSON")
    return "\n".join(lines[1:-1]).strip()


def validate_breakdown_result(
    data: dict[str, Any], *, allow_legacy_candidate_defaults: bool = False
) -> TaskBreakdownResult:
    required = {
        "decision",
        "candidates",
        "rejected_items",
        "global_contract_summary",
        "global_constraints",
        "verification",
        "non_goals",
        "recommended_sequence",
        "confidence",
        "rationale",
        "source",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise TaskBreakdownValidationError(f"task breakdown missing fields: {', '.join(missing)}")
    decision = data["decision"]
    if decision not in {"single_task", "proposed_task_breakdown"}:
        raise TaskBreakdownValidationError("decision must be single_task or proposed_task_breakdown")
    candidates = _validate_candidates(
        data["candidates"], allow_legacy_candidate_defaults=allow_legacy_candidate_defaults
    )
    if not candidates:
        raise TaskBreakdownValidationError("at least one candidate is required")
    confidence = data["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, int | float) or not 0 <= float(confidence) <= 1:
        raise TaskBreakdownValidationError("confidence must be a number between 0 and 1")
    if data["source"] != "llm":
        raise TaskBreakdownValidationError("source must be llm")
    rationale = data["rationale"]
    if not isinstance(rationale, str):
        raise TaskBreakdownValidationError("rationale must be a string")
    global_contract_summary = data["global_contract_summary"]
    if not isinstance(global_contract_summary, str):
        raise TaskBreakdownValidationError("global_contract_summary must be a string")
    return TaskBreakdownResult(
        decision=decision,
        candidates=candidates,
        rejected_items=_validate_rejected_items(data["rejected_items"]),
        global_contract_summary=global_contract_summary.strip(),
        global_constraints=_validate_string_array(data["global_constraints"], "global_constraints"),
        verification=_validate_string_array(data["verification"], "verification"),
        non_goals=_validate_string_array(data["non_goals"], "non_goals"),
        recommended_sequence=_validate_string_array(data["recommended_sequence"], "recommended_sequence"),
        confidence=float(confidence),
        rationale=rationale,
        source=data["source"],
    )


def _validate_candidates(value: Any, *, allow_legacy_candidate_defaults: bool) -> list[BreakdownCandidate]:
    if not isinstance(value, list):
        raise TaskBreakdownValidationError("candidates must be an array")
    candidates: list[BreakdownCandidate] = []
    for item in value:
        if not isinstance(item, dict):
            raise TaskBreakdownValidationError("candidate must be an object")
        title = item.get("title")
        prompt = item.get("prompt")
        acceptance_criteria = item.get("acceptance_criteria")
        kind = item.get("kind", "implementation")
        if kind not in TASK_BREAKDOWN_CANDIDATE_KINDS:
            raise TaskBreakdownValidationError(
                "candidate kind must be implementation or acceptance_verification"
            )
        if not isinstance(title, str) or not title.strip():
            raise TaskBreakdownValidationError("candidate title must be a non-empty string")
        if not isinstance(prompt, str) or not prompt.strip():
            raise TaskBreakdownValidationError("candidate prompt must be a non-empty string")
        acceptance_criteria = _string_or_joined_strings(acceptance_criteria, "candidate acceptance_criteria")
        human_in_loop = item.get("human_in_loop", None)
        execution_mode = _validate_execution_mode(
            item.get("execution_mode", None),
            human_in_loop,
            allow_legacy_default=allow_legacy_candidate_defaults,
        )
        if human_in_loop is None:
            human_in_loop = execution_mode == "HITL"
        if not isinstance(human_in_loop, bool):
            raise TaskBreakdownValidationError("candidate human_in_loop must be a boolean")
        if human_in_loop != (execution_mode == "HITL"):
            raise TaskBreakdownValidationError(
                "candidate human_in_loop must match execution_mode HITL"
            )
        hitl_reason = _optional_string(item.get("hitl_reason"), "candidate hitl_reason")
        if execution_mode == "HITL" and not hitl_reason:
            hitl_reason = "Requires operator review or judgment before completion."
        if execution_mode == "AFK" and hitl_reason:
            raise TaskBreakdownValidationError("candidate hitl_reason must be empty for AFK")
        candidates.append(
            BreakdownCandidate(
                kind=kind,
                title=title.strip(),
                objective=_candidate_text(
                    item,
                    "objective",
                    fallback=prompt.strip(),
                    field="candidate objective",
                    allow_legacy_default=allow_legacy_candidate_defaults,
                ),
                prompt=prompt.strip(),
                acceptance_criteria=acceptance_criteria,
                constraints=_validate_string_array(item.get("constraints", []), "candidate constraints"),
                proof=_candidate_text(
                    item,
                    "proof",
                    fallback=acceptance_criteria or "No candidate-specific proof supplied; use global verification.",
                    field="candidate proof",
                    allow_legacy_default=allow_legacy_candidate_defaults,
                ),
                why_this_task_exists=_candidate_text(
                    item,
                    "why_this_task_exists",
                    fallback=f"{title.strip()} is a distinct board-card candidate from the source contract.",
                    field="candidate why_this_task_exists",
                    allow_legacy_default=allow_legacy_candidate_defaults,
                ),
                why_not_smaller=_candidate_text(
                    item,
                    "why_not_smaller",
                    fallback="Smaller substeps would not be independently useful and verifiable.",
                    field="candidate why_not_smaller",
                    allow_legacy_default=allow_legacy_candidate_defaults,
                ),
                why_not_larger=_candidate_text(
                    item,
                    "why_not_larger",
                    fallback="Merging this with adjacent work would broaden the Worker prompt and weaken reviewability.",
                    field="candidate why_not_larger",
                    allow_legacy_default=allow_legacy_candidate_defaults,
                ),
                dependencies=_candidate_string_array(
                    item,
                    "dependencies",
                    "candidate dependencies",
                    allow_legacy_default=allow_legacy_candidate_defaults,
                ),
                likely_entry_points=_candidate_string_array(
                    item,
                    "likely_entry_points",
                    "candidate likely_entry_points",
                    allow_legacy_default=allow_legacy_candidate_defaults,
                ),
                execution_mode=execution_mode,
                hitl_reason=hitl_reason,
                human_in_loop=human_in_loop,
            )
        )
    return candidates


def _validate_execution_mode(value: Any, human_in_loop: Any, *, allow_legacy_default: bool) -> str:
    if value is None or value == "":
        if not allow_legacy_default:
            raise TaskBreakdownValidationError("candidate execution_mode is required")
        return "HITL" if human_in_loop is not False else "AFK"
    if not isinstance(value, str):
        raise TaskBreakdownValidationError("candidate execution_mode must be AFK or HITL")
    mode = value.strip().upper()
    if mode not in TASK_BREAKDOWN_EXECUTION_MODES:
        raise TaskBreakdownValidationError("candidate execution_mode must be AFK or HITL")
    return mode


def _candidate_text(
    item: dict[str, Any], key: str, *, fallback: str, field: str, allow_legacy_default: bool
) -> str:
    if key not in item or item.get(key) is None:
        if not allow_legacy_default:
            raise TaskBreakdownValidationError(f"{field} is required")
        return fallback.strip()
    value = item.get(key)
    text = _string_or_joined_strings(value, field)
    if not text:
        raise TaskBreakdownValidationError(f"{field} must be non-empty when supplied")
    return text


def _candidate_string_array(
    item: dict[str, Any], key: str, field: str, *, allow_legacy_default: bool
) -> list[str]:
    if key not in item or item.get(key) is None:
        if not allow_legacy_default:
            raise TaskBreakdownValidationError(f"{field} is required")
        return []
    return _validate_string_array(item.get(key), field)


def _optional_string(value: Any, field: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TaskBreakdownValidationError(f"{field} must be a string")
    return value.strip()


def _validate_rejected_items(value: Any) -> list[RejectedBreakdownItem]:
    if not isinstance(value, list):
        raise TaskBreakdownValidationError("rejected_items must be an array")
    rejected: list[RejectedBreakdownItem] = []
    for item in value:
        if not isinstance(item, dict):
            raise TaskBreakdownValidationError("rejected item must be an object")
        text = item.get("text")
        reason = item.get("reason")
        if not isinstance(text, str) or not text.strip():
            raise TaskBreakdownValidationError("rejected item text must be a non-empty string")
        if not isinstance(reason, str) or not reason.strip():
            raise TaskBreakdownValidationError("rejected item reason must be a non-empty string")
        rejected.append(RejectedBreakdownItem(text=text.strip(), reason=reason.strip()))
    return rejected


def _validate_string_array(value: Any, field: str) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TaskBreakdownValidationError(f"{field} must be an array of strings")
    return [item.strip() for item in value if item.strip()]


def _string_or_joined_strings(value: Any, field: str) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return "\n".join(item.strip() for item in value if item.strip())
    raise TaskBreakdownValidationError(f"{field} must be a string or array of strings")


def _response_content(response: Any) -> str:
    payload = response_to_dict(response)
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise TaskBreakdownValidationError("task breakdown response missing choices")
    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise TaskBreakdownValidationError("task breakdown response missing content")
    return content
