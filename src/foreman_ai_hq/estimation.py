from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from foreman_ai_hq.estimation_calibration import build_calibration_selection
from foreman_ai_hq.guardrails import GuardrailConfig
from foreman_ai_hq.llm import response_to_dict
from foreman_ai_hq.repo_context import build_repo_context_brief


@dataclass(frozen=True)
class EstimateResult:
    token_estimate: int
    complexity: str
    confidence: float
    rationale: str
    assumptions: list[str]
    risk_flags: list[str]
    budget_note: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "token_estimate": self.token_estimate,
            "complexity": self.complexity,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "assumptions": self.assumptions,
            "risk_flags": self.risk_flags,
            "budget_note": self.budget_note,
            "source": self.source,
        }


class EstimatorError(Exception):
    """Base class for estimator failures that require manual estimate."""


class EstimatorUnavailableError(EstimatorError):
    """Raised when the estimator LLM call fails."""


class EstimatorValidationError(EstimatorError):
    """Raised when the estimator response is not valid structured JSON."""


async def estimate_task(
    description: str,
    config: GuardrailConfig,
    *,
    llm_client: Any,
    estimator_model: str,
    remaining_daily_tokens: int | None = None,
    daily_cap_tokens: int | None = None,
    project_root: str | None = None,
    project_profile: dict[str, Any] | None = None,
) -> tuple[EstimateResult, Any]:
    project_context = _build_project_context(project_root)
    # Calibration examples nudge estimates without overriding the LLM's final structured response.
    calibration_context = _build_calibration_context(
        description,
        project_root=project_root,
        project_profile=project_profile,
    )
    user_payload: dict[str, Any] = {
        "task_description": description,
        "remaining_daily_tokens": remaining_daily_tokens,
        "daily_cap_tokens": daily_cap_tokens,
    }
    if project_context:
        user_payload["project_context"] = project_context
    if calibration_context:
        user_payload["calibration_context"] = calibration_context
    request = {
        "model": estimator_model,
        "messages": [
            {"role": "system", "content": _system_prompt(config, project_context, calibration_context)},
            {
                "role": "user",
                "content": json.dumps(user_payload, sort_keys=True),
            },
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    try:
        response = await llm_client.acompletion(request)
    except Exception as exc:  # pragma: no cover - exercised through route tests
        raise EstimatorUnavailableError(str(exc)) from exc
    return _parse_response(response, config), response


def _build_project_context(project_root: str | None) -> str:
    """Build a compact project context brief for the estimator.

    Returns empty string when project_root is None, missing, or unreadable
    — the estimator is designed to work without context.
    """
    if not project_root:
        return ""
    try:
        brief = build_repo_context_brief(project_root)
    except (OSError, ValueError):
        return ""
    text = str(brief.get("text") or "").strip()
    # Keep estimator prompts bounded even when repository context is large.
    return text[:8_000]


def _build_calibration_context(
    description: str,
    *,
    project_root: str | None,
    project_profile: dict[str, Any] | None,
) -> str:
    try:
        selection = build_calibration_selection(
            task_description=description,
            project_root=project_root,
            project_profile=project_profile,
        )
    except OSError:
        return ""
    return selection.summary


def _system_prompt(config: GuardrailConfig, project_context: str = "", calibration_context: str = "") -> str:
    routing = {
        name: {
            "description": route.description,
        }
        for name, route in config.model_routing.task_complexity.items()
    }
    clamp = config.model_routing.budget_aware_clamp
    prompt = (
        "You estimate software task implementation token budgets. Return ONLY valid JSON "
        "with exactly these fields: token_estimate (positive integer), complexity "
        "(simple|modest|complex), confidence (number 0-1), "
        "rationale (string), assumptions (array of strings), risk_flags (array of strings), "
        "budget_note (string), source (string, use 'llm'). "
        "Do not choose or recommend a Worker model; deterministic adapter-aware routing handles that after estimation. "
        "Do not include markdown or extra keys. Complexity policy: "
        f"{json.dumps(routing, sort_keys=True)}. Budget clamp: "
        f"enabled={clamp.enabled}, remaining_daily_threshold={clamp.remaining_daily_threshold}, "
        f"note_template={clamp.note!r}."
    )
    if project_context:
        prompt += (
            "\n\nProject context (use to ground your estimate in real project surface):\n"
            f"{project_context}"
        )
    if calibration_context:
        prompt += (
            "\n\nEstimation calibration context (examples only; do not directly multiply, clamp, "
            "or override the final token estimate):\n"
            f"{calibration_context}"
        )
    return prompt


def _parse_response(response: Any, config: GuardrailConfig) -> EstimateResult:
    try:
        data = json.loads(_estimator_json_text(_response_content(response)))
    except Exception as exc:
        raise EstimatorValidationError("estimator returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise EstimatorValidationError("estimator JSON must be an object")
    return _validate_result(data, config)


def _estimator_json_text(content: str) -> str:
    text = content.strip()
    if not text.startswith("```"):
        return text

    # Accept a fenced JSON object because some providers wrap json_object responses anyway.
    lines = text.splitlines()
    if len(lines) < 3:
        raise EstimatorValidationError("estimator returned invalid JSON")
    opening = lines[0].strip()
    language = opening[3:].strip().lower()
    if language not in {"", "json"}:
        raise EstimatorValidationError("estimator returned invalid JSON")
    if lines[-1].strip() != "```":
        raise EstimatorValidationError("estimator returned invalid JSON")
    return "\n".join(lines[1:-1]).strip()


def _response_content(response: Any) -> str:
    payload = response_to_dict(response)
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise EstimatorValidationError("estimator response missing choices")
    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise EstimatorValidationError("estimator response missing content")
    return content


def _validate_result(data: dict[str, Any], config: GuardrailConfig) -> EstimateResult:
    required = {
        "token_estimate",
        "complexity",
        "confidence",
        "rationale",
        "assumptions",
        "risk_flags",
        "budget_note",
        "source",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise EstimatorValidationError(f"estimator response missing fields: {', '.join(missing)}")
    extra = sorted(data.keys() - required)
    if extra:
        raise EstimatorValidationError(f"estimator response included extra fields: {', '.join(extra)}")
    token_estimate = data["token_estimate"]
    if isinstance(token_estimate, bool) or not isinstance(token_estimate, int) or token_estimate <= 0:
        raise EstimatorValidationError("token_estimate must be a positive integer")
    complexity = data["complexity"]
    if complexity not in config.model_routing.task_complexity:
        allowed_complexities = ", ".join(sorted(config.model_routing.task_complexity))
        raise EstimatorValidationError(f"complexity must be one of: {allowed_complexities}")
    confidence = data["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, int | float) or not 0 <= float(confidence) <= 1:
        raise EstimatorValidationError("confidence must be a number between 0 and 1")
    for key in ["rationale", "budget_note", "source"]:
        if not isinstance(data[key], str):
            raise EstimatorValidationError(f"{key} must be a string")
    for key in ["assumptions", "risk_flags"]:
        if not isinstance(data[key], list) or not all(isinstance(item, str) for item in data[key]):
            raise EstimatorValidationError(f"{key} must be an array of strings")
    if data["source"] != "llm":
        raise EstimatorValidationError("source must be llm")
    return EstimateResult(
        token_estimate=token_estimate,
        complexity=complexity,
        confidence=float(confidence),
        rationale=data["rationale"],
        assumptions=data["assumptions"],
        risk_flags=data["risk_flags"],
        budget_note=data["budget_note"],
        source=data["source"],
    )
