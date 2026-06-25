from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from agile_ai_htb.guardrails import GuardrailConfig
from agile_ai_htb.llm import response_to_dict
from agile_ai_htb.repo_context import build_repo_context_brief


@dataclass(frozen=True)
class EstimateResult:
    token_estimate: int
    complexity: str
    recommended_model: str
    confidence: float
    rationale: str
    assumptions: list[str]
    risk_flags: list[str]
    spike_recommendation: str
    budget_note: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "token_estimate": self.token_estimate,
            "complexity": self.complexity,
            "recommended_model": self.recommended_model,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "assumptions": self.assumptions,
            "risk_flags": self.risk_flags,
            "spike_recommendation": self.spike_recommendation,
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
) -> tuple[EstimateResult, Any]:
    project_context = _build_project_context(project_root)
    user_payload: dict[str, Any] = {
        "task_description": description,
        "remaining_daily_tokens": remaining_daily_tokens,
        "daily_cap_tokens": daily_cap_tokens,
    }
    if project_context:
        user_payload["project_context"] = project_context
    request = {
        "model": estimator_model,
        "messages": [
            {"role": "system", "content": _system_prompt(config, project_context)},
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
    return text[:8_000]


def _system_prompt(config: GuardrailConfig, project_context: str = "") -> str:
    routing = {
        name: {
            "description": route.description,
            "recommended_model": route.recommended_model,
        }
        for name, route in config.model_routing.task_complexity.items()
    }
    clamp = config.model_routing.budget_aware_clamp
    prompt = (
        "You estimate software task implementation token budgets. Return ONLY valid JSON "
        "with exactly these fields: token_estimate (positive integer), complexity "
        "(simple|modest|complex), recommended_model (string), confidence (number 0-1), "
        "rationale (string), assumptions (array of strings), risk_flags (array of strings), "
        "spike_recommendation (string), budget_note (string), source (string, use 'llm'). "
        "Do not include markdown or extra keys. Light routing policy: "
        f"{json.dumps(routing, sort_keys=True)}. Budget clamp: "
        f"enabled={clamp.enabled}, remaining_daily_threshold={clamp.remaining_daily_threshold}, "
        f"note_template={clamp.note!r}."
    )
    if project_context:
        prompt += (
            "\n\nProject context (use to ground your estimate in real project surface):\n"
            f"{project_context}"
        )
    return prompt


def _parse_response(response: Any, config: GuardrailConfig) -> EstimateResult:
    try:
        data = json.loads(_response_content(response))
    except Exception as exc:
        raise EstimatorValidationError("estimator returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise EstimatorValidationError("estimator JSON must be an object")
    return _validate_result(data, config)


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
        "recommended_model",
        "confidence",
        "rationale",
        "assumptions",
        "risk_flags",
        "spike_recommendation",
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
    recommended_model = data["recommended_model"]
    if not isinstance(recommended_model, str) or not recommended_model.strip():
        raise EstimatorValidationError("recommended_model must be a non-empty string")
    allowed_models = {
        route.recommended_model for route in config.model_routing.task_complexity.values()
    }
    if recommended_model not in allowed_models:
        raise EstimatorValidationError("recommended_model must be configured for task routing")
    confidence = data["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, int | float) or not 0 <= float(confidence) <= 1:
        raise EstimatorValidationError("confidence must be a number between 0 and 1")
    for key in ["rationale", "spike_recommendation", "budget_note", "source"]:
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
        recommended_model=recommended_model,
        confidence=float(confidence),
        rationale=data["rationale"],
        assumptions=data["assumptions"],
        risk_flags=data["risk_flags"],
        spike_recommendation=data["spike_recommendation"],
        budget_note=data["budget_note"],
        source=data["source"],
    )
