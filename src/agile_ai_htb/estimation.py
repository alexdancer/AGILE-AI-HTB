from __future__ import annotations

from dataclasses import dataclass

from agile_ai_htb.guardrails import GuardrailConfig


@dataclass(frozen=True)
class EstimateResult:
    token_estimate: int
    complexity: str
    recommended_model: str
    budget_note: str | None = None

    def as_dict(self) -> dict[str, int | str | None]:
        return {
            "token_estimate": self.token_estimate,
            "complexity": self.complexity,
            "recommended_model": self.recommended_model,
            "budget_note": self.budget_note,
        }


def estimate_task(
    description: str,
    config: GuardrailConfig,
    *,
    remaining_daily_tokens: int | None = None,
    daily_cap_tokens: int | None = None,
) -> EstimateResult:
    complexity = _classify(description)
    token_estimate = {"simple": 5_000, "modest": 25_000, "complex": 100_000}[complexity]
    recommended_complexity = complexity
    budget_note = None

    clamp = config.model_routing.budget_aware_clamp
    if (
        clamp.enabled
        and remaining_daily_tokens is not None
        and daily_cap_tokens
        and remaining_daily_tokens / daily_cap_tokens < clamp.remaining_daily_threshold
    ):
        recommended_complexity = _downgrade(complexity)
        original = _model_for(config, complexity)
        downgraded = _model_for(config, recommended_complexity)
        if downgraded != original:
            budget_note = clamp.note.format(original=original, downgraded=downgraded)

    return EstimateResult(
        token_estimate=token_estimate,
        complexity=complexity,
        recommended_model=_model_for(config, recommended_complexity),
        budget_note=budget_note,
    )


def _classify(description: str) -> str:
    normalized = description.lower()
    words = normalized.split()
    complex_keywords = {
        "architecture",
        "auth",
        "authentication",
        "migration",
        "migrations",
        "streaming",
        "proxy",
        "refactor",
        "design",
        "database",
    }
    modest_keywords = {"endpoint", "api", "tests", "route", "sqlite", "session", "integration"}
    if len(words) >= 12 or any(keyword in normalized for keyword in complex_keywords):
        return "complex"
    if len(words) >= 5 or any(keyword in normalized for keyword in modest_keywords):
        return "modest"
    return "simple"


def _downgrade(complexity: str) -> str:
    order = ["simple", "modest", "complex"]
    index = order.index(complexity)
    return order[max(index - 1, 0)]


def _model_for(config: GuardrailConfig, complexity: str) -> str:
    configured = config.model_routing.task_complexity.get(complexity)
    if configured is None:
        return "claude-haiku"
    return configured.recommended_model
