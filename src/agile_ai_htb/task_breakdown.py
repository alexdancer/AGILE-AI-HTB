from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from agile_ai_htb.llm import response_to_dict

TASK_BREAKDOWN_CANDIDATE_KINDS = {"implementation", "acceptance_verification"}


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
    prompt: str
    acceptance_criteria: str
    constraints: list[str]
    human_in_loop: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "title": self.title,
            "prompt": self.prompt,
            "acceptance_criteria": self.acceptance_criteria,
            "constraints": self.constraints,
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
) -> tuple[TaskBreakdownResult, Any]:
    request = {
        "model": task_breakdown_model,
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "source_text": source_text,
                        "intake_metadata": intake_metadata or {},
                        "structure_hints": structure_hints or [],
                    },
                    sort_keys=True,
                ),
            },
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    try:
        response = await llm_client.acompletion(request)
    except Exception as exc:  # pragma: no cover - exercised through route tests
        raise TaskBreakdownUnavailableError(str(exc)) from exc
    return _parse_response(response), response


def _system_prompt() -> str:
    return (
        "You are the AGILE-AI-HTB Task Breakdown Agent. Classify Markdown or oversized coding-task input "
        "into independently grabbable vertical-slice task candidates. Markdown bullets are evidence, not tasks. "
        "Return ONLY valid JSON with exactly these fields: decision (single_task|proposed_task_breakdown), "
        "candidates (array of objects with kind, title, prompt, acceptance_criteria, constraints array, human_in_loop boolean), "
        "rejected_items (array of objects with text and reason), global_contract_summary (string), global_constraints (array of strings), "
        "verification (array of strings), non_goals (array of strings), recommended_sequence (array of candidate titles), "
        "confidence (number 0-1), rationale (string), source (string, use 'llm'). "
        "Classify every candidate kind as either 'implementation' or 'acceptance_verification'. "
        "For multi-slice breakdowns that produce one integrated artifact (CLI, app, API, demo, report, or similar), "
        "include one acceptance_verification candidate recommended last. That candidate must verify the combined artifact "
        "against the original source contract using the smallest executable proof available; it must not ask the Worker to "
        "reimplement the whole source task as one oversized implementation task. "
        "Write one concise global_contract_summary describing what all accepted slices must collectively satisfy. "
        "Do not turn constraints like 'Do not add network dependencies.' or verification like 'Run pytest.' into standalone tasks."
    )


def _parse_response(response: Any) -> TaskBreakdownResult:
    try:
        data = json.loads(_response_content(response))
    except Exception as exc:
        raise TaskBreakdownValidationError("task breakdown returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise TaskBreakdownValidationError("task breakdown JSON must be an object")
    return validate_breakdown_result(data)


def validate_breakdown_result(data: dict[str, Any]) -> TaskBreakdownResult:
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
    candidates = _validate_candidates(data["candidates"])
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


def _validate_candidates(value: Any) -> list[BreakdownCandidate]:
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
        human_in_loop = item.get("human_in_loop", True)
        if not isinstance(human_in_loop, bool):
            raise TaskBreakdownValidationError("candidate human_in_loop must be a boolean")
        candidates.append(
            BreakdownCandidate(
                kind=kind,
                title=title.strip(),
                prompt=prompt.strip(),
                acceptance_criteria=acceptance_criteria,
                constraints=_validate_string_array(item.get("constraints", []), "candidate constraints"),
                human_in_loop=human_in_loop,
            )
        )
    return candidates


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
