from pathlib import Path

from agile_ai_htb.guardrails import load_guardrails
from agile_ai_htb.model_routing import route_worker_model

ROOT = Path(__file__).resolve().parents[2]


def _config():
    return load_guardrails(ROOT / "guardrails.yaml")


def _adapter(models):
    return {"id": "opencode", "supported_models": list(models)}


def test_route_worker_model_selects_guardrail_model_when_adapter_allows_it():
    result = route_worker_model(
        _config(),
        complexity="simple",
        estimate_tokens=2_000,
        remaining_daily_tokens=None,
        daily_cap_tokens=None,
        adapter=_adapter(["claude-haiku-4-5", "opencode/other"]),
        allowed_models=["claude-haiku-4-5", "opencode/other"],
    )

    assert result.selected_model == "claude-haiku-4-5"
    assert result.metadata["model_routing"]["guardrail_policy_model"] == "claude-haiku-4-5"
    assert result.metadata["worker_model_constraint"]["reason"] == "guardrail_policy_model_allowed"


def test_route_worker_model_ranks_adapter_allowed_fallback_for_small_tasks():
    result = route_worker_model(
        _config(),
        complexity="simple",
        estimate_tokens=2_000,
        remaining_daily_tokens=None,
        daily_cap_tokens=None,
        adapter=_adapter(["opencode/big-pickle", "opencode/claude-haiku-4-5", "opencode/gpt-5.4-mini"]),
        allowed_models=["opencode/big-pickle", "opencode/claude-haiku-4-5", "opencode/gpt-5.4-mini"],
    )

    assert result.selected_model == "opencode/claude-haiku-4-5"
    assert result.metadata["worker_model_constraint"]["reason"] == "guardrail_policy_model_not_allowed_ranked"


def test_route_worker_model_preserves_first_allowed_model_for_large_tasks():
    result = route_worker_model(
        _config(),
        complexity="complex",
        estimate_tokens=80_000,
        remaining_daily_tokens=None,
        daily_cap_tokens=None,
        adapter=_adapter(["opencode/big-pickle", "opencode/claude-haiku-4-5"]),
        allowed_models=["opencode/big-pickle", "opencode/claude-haiku-4-5"],
    )

    assert result.selected_model == "opencode/big-pickle"
    assert result.metadata["worker_model_constraint"]["reason"] == "guardrail_policy_model_not_allowed"


def test_route_worker_model_returns_no_recommendation_without_allowed_models():
    result = route_worker_model(
        _config(),
        complexity="modest",
        estimate_tokens=12_000,
        remaining_daily_tokens=None,
        daily_cap_tokens=None,
        adapter=_adapter([]),
        allowed_models=[],
    )

    assert result.selected_model is None
    assert result.metadata["worker_model_constraint"] == {
        "state": "no_allowed_models",
        "adapter_id": "opencode",
        "available_models": [],
        "original_complexity": "modest",
        "routing_tier": "modest",
        "guardrail_policy_model": "claude-sonnet-4-6",
        "original_model": "claude-sonnet-4-6",
        "budget_clamped": False,
        "selected_model": None,
        "reason": "no_allowed_worker_models",
        "setup_required": "Approve at least one allowed Worker model before launch.",
    }


def test_route_worker_model_returns_no_recommendation_without_adapter():
    result = route_worker_model(
        _config(),
        complexity="modest",
        estimate_tokens=12_000,
        remaining_daily_tokens=None,
        daily_cap_tokens=None,
        adapter=None,
        allowed_models=[],
    )

    assert result.selected_model is None
    assert result.metadata["worker_model_constraint"]["state"] == "no_adapter"
    assert result.metadata["worker_model_constraint"]["selected_model"] is None


def test_route_worker_model_budget_clamps_before_adapter_selection():
    result = route_worker_model(
        _config(),
        complexity="complex",
        estimate_tokens=80_000,
        remaining_daily_tokens=1_000,
        daily_cap_tokens=100_000,
        adapter=_adapter(["claude-sonnet-4-6", "claude-opus-4-8"]),
        allowed_models=["claude-sonnet-4-6", "claude-opus-4-8"],
    )

    assert result.selected_model == "claude-sonnet-4-6"
    constraint = result.metadata["worker_model_constraint"]
    assert constraint["budget_clamped"] is True
    assert constraint["pre_clamp_tier"] == "complex"
    assert constraint["routing_tier"] == "modest"
    assert constraint["guardrail_policy_model"] == "claude-sonnet-4-6"
