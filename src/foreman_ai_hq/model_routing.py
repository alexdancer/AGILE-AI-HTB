from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from foreman_ai_hq.guardrails import GuardrailConfig

_COMPLEXITY_ORDER = ["simple", "modest", "complex"]


@dataclass(frozen=True)
class WorkerModelRoutingResult:
    selected_model: str | None
    metadata: dict[str, Any]


def route_worker_model(
    config: GuardrailConfig,
    *,
    complexity: str,
    estimate_tokens: int | None,
    remaining_daily_tokens: int | None,
    daily_cap_tokens: int | None,
    adapter: dict[str, Any] | None,
    allowed_models: list[str],
) -> WorkerModelRoutingResult:
    """Choose a launch-compatible Worker model for an estimated task.

    The estimator owns sizing and complexity. This router owns Worker model
    choice and only returns models approved for the selected/default adapter.
    """

    original_tier = _normalized_tier(complexity, config)
    routing_tier, clamp_metadata = _budget_clamped_tier(
        original_tier,
        config,
        remaining_daily_tokens=remaining_daily_tokens,
        daily_cap_tokens=daily_cap_tokens,
    )
    guardrail_candidate = config.model_routing.task_complexity[routing_tier].recommended_model
    # Keep the policy choice and adapter constraint together so blocked launches explain what narrowed the model list.
    base_constraint: dict[str, Any] = {
        "state": "constrained_by_allowed_models",
        "adapter_id": adapter.get("id") if adapter else None,
        "available_models": list(allowed_models),
        "original_complexity": original_tier,
        "routing_tier": routing_tier,
        "guardrail_policy_model": guardrail_candidate,
        # Backward-compatible key used by existing task metadata assertions.
        "original_model": guardrail_candidate,
        **clamp_metadata,
    }
    if not adapter:
        base_constraint.update(
            {
                "state": "no_adapter",
                "selected_model": None,
                "reason": "no_worker_adapter_available",
                "setup_required": "Configure a Worker Adapter before launch.",
            }
        )
        return _result(None, base_constraint)
    if not allowed_models:
        base_constraint.update(
            {
                "state": "no_allowed_models",
                "selected_model": None,
                "reason": "no_allowed_worker_models",
                "setup_required": "Approve at least one allowed Worker model before launch.",
            }
        )
        return _result(None, base_constraint)
    if guardrail_candidate in allowed_models:
        base_constraint.update(
            {
                "selected_model": guardrail_candidate,
                "reason": "guardrail_policy_model_allowed",
            }
        )
        return _result(guardrail_candidate, base_constraint)

    # If policy's preferred model is unavailable, pick from the adapter allowlist rather than broadening scope.
    selected_model = rank_allowed_worker_model(
        allowed_models,
        estimate_tokens=estimate_tokens,
        complexity=routing_tier,
    )
    reason = "guardrail_policy_model_not_allowed"
    if selected_model != allowed_models[0]:
        reason = "guardrail_policy_model_not_allowed_ranked"
    base_constraint.update({"selected_model": selected_model, "reason": reason})
    return _result(selected_model, base_constraint)


def rank_allowed_worker_model(
    models: list[str], *, estimate_tokens: int | None, complexity: str | None
) -> str:
    if not models:
        raise ValueError("models must not be empty")
    normalized_complexity = (complexity or "").strip().lower()
    lightweight_task = (estimate_tokens is not None and estimate_tokens <= 10_000) or normalized_complexity in {
        "simple",
        "modest",
        "small",
        "low",
    }
    if not lightweight_task:
        return str(models[0])

    def score(model: str, index: int) -> tuple[int, int]:
        # Prefer smaller/cheaper model names for lightweight work while preserving input order as tiebreaker.
        lowered = model.lower()
        if any(term in lowered for term in ("haiku", "mini", "nano", "flash")):
            return (0, index)
        if any(term in lowered for term in ("big-pickle", "opus", "pro", "max")):
            return (20, index)
        return (10, index)

    return min(((str(model), index) for index, model in enumerate(models)), key=lambda item: score(item[0], item[1]))[0]


def _result(selected_model: str | None, constraint: dict[str, Any]) -> WorkerModelRoutingResult:
    return WorkerModelRoutingResult(
        selected_model=selected_model,
        metadata={
            "worker_model_constraint": constraint,
            # Newer views read the flatter model_routing summary; the full constraint remains for diagnostics.
            "model_routing": {
                "selected_adapter_id": constraint.get("adapter_id"),
                "selected_model": selected_model,
                "original_complexity": constraint.get("original_complexity"),
                "routing_tier": constraint.get("routing_tier"),
                "guardrail_policy_model": constraint.get("guardrail_policy_model"),
                "state": constraint.get("state"),
                "reason": constraint.get("reason"),
                "budget_clamped": bool(constraint.get("budget_clamped")),
            },
        },
    )


def _normalized_tier(complexity: str, config: GuardrailConfig) -> str:
    normalized = (complexity or "").strip().lower()
    if normalized in config.model_routing.task_complexity:
        return normalized
    # Unknown estimator output falls back to a configured middle tier instead of failing launch routing.
    return "modest" if "modest" in config.model_routing.task_complexity else next(iter(config.model_routing.task_complexity))


def _budget_clamped_tier(
    tier: str,
    config: GuardrailConfig,
    *,
    remaining_daily_tokens: int | None,
    daily_cap_tokens: int | None,
) -> tuple[str, dict[str, Any]]:
    clamp = config.model_routing.budget_aware_clamp
    metadata: dict[str, Any] = {"budget_clamped": False}
    if not clamp.enabled or remaining_daily_tokens is None or not daily_cap_tokens or daily_cap_tokens <= 0:
        return tier, metadata
    remaining_ratio = remaining_daily_tokens / daily_cap_tokens
    metadata["remaining_daily_ratio"] = remaining_ratio
    if remaining_ratio >= clamp.remaining_daily_threshold:
        return tier, metadata
    try:
        current_index = _COMPLEXITY_ORDER.index(tier)
    except ValueError:
        return tier, metadata
    if current_index <= 0:
        return tier, metadata
    # Clamp by one tier only; it is a budget hint, not permission to downgrade arbitrarily.
    clamped_tier = _COMPLEXITY_ORDER[current_index - 1]
    if clamped_tier not in config.model_routing.task_complexity:
        return tier, metadata
    return clamped_tier, {
        **metadata,
        "budget_clamped": True,
        "budget_clamp_note": clamp.note,
        "budget_clamp_threshold": clamp.remaining_daily_threshold,
        "pre_clamp_tier": tier,
        "routing_tier": clamped_tier,
    }
