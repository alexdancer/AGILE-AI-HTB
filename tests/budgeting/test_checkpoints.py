from dataclasses import replace

from agile_ai_htb.checkpoints import evaluate_checkpoints
from agile_ai_htb.guardrails import load_guardrails


def _artifact(**overrides):
    artifact = {
        "session": {"id": "sess-1"},
        "token_log": [
            {"total_tokens": 10_000},
            {"total_tokens": 15_000},
        ],
        "tool_trace": [
            {"tool_name": "read_file"},
            {"tool_name": "terminal"},
            {"tool_name": "web_search"},
        ],
        "alarms": [],
        "guardrail_snapshots": [],
        "checkpoint_results": [],
    }
    artifact.update(overrides)
    return artifact


def _by_name(results):
    return {result.name: result for result in results}


def test_evaluate_checkpoints_passes_clean_artifact():
    config = load_guardrails("guardrails.yaml")

    results = _by_name(evaluate_checkpoints(_artifact(), config))

    assert results["budget_health"].passed is True
    assert results["stuck_loop_score"].passed is True
    assert results["tool_diversity"].passed is True
    assert results["timeout_respect"].passed is True
    assert all(result.details for result in results.values())


def test_budget_health_fails_when_session_spend_exceeds_cap():
    config = load_guardrails("guardrails.yaml")
    artifact = _artifact(token_log=[{"total_tokens": 150_000}, {"total_tokens": 75_000}])

    result = _by_name(evaluate_checkpoints(artifact, config))["budget_health"]

    assert result.passed is False
    assert result.details["session_tokens"] == 225_000
    assert result.details["session_cap_tokens"] == 200_000


def test_budget_health_uses_fair_share_when_session_cap_disabled():
    config = load_guardrails("guardrails.yaml")
    disabled_cap = replace(config, session_cap=replace(config.session_cap, enabled=False))
    artifact = _artifact(
        token_log=[{"total_tokens": 60_000}],
        budget={"remaining_daily_tokens": 100_000, "fair_share_factor": 0.5},
    )

    result = _by_name(evaluate_checkpoints(artifact, disabled_cap))["budget_health"]

    assert result.passed is False
    assert result.details["budget_limit_source"] == "fair_share"
    assert result.details["budget_limit_tokens"] == 50_000


def test_stuck_loop_score_fails_with_three_loop_alarms():
    config = load_guardrails("guardrails.yaml")
    artifact = _artifact(
        alarms=[
            {"type": "LOOP_DETECTED"},
            {"type": "BUDGET_YELLOW"},
            {"type": "LOOP_DETECTED"},
            {"type": "LOOP_DETECTED"},
        ]
    )

    result = _by_name(evaluate_checkpoints(artifact, config))["stuck_loop_score"]

    assert result.passed is False
    assert result.details["loop_alarm_count"] == 3


def test_tool_diversity_fails_with_less_than_three_categories_unless_red_zone_restricted():
    config = load_guardrails("guardrails.yaml")
    low_diversity = _artifact(tool_trace=[{"tool_name": "read_file"}, {"tool_name": "patch"}])
    red_restricted = _artifact(
        tool_trace=[{"tool_name": "read_file"}, {"tool_name": "patch"}],
        guardrail_snapshots=[{"zone": "red", "decision": {"blocked_tools": ["web_search"]}}],
    )

    low = _by_name(evaluate_checkpoints(low_diversity, config))["tool_diversity"]
    red = _by_name(evaluate_checkpoints(red_restricted, config))["tool_diversity"]

    assert low.passed is False
    assert low.details["distinct_categories"] == 1
    assert red.passed is True
    assert red.details["red_zone_restricted"] is True


def test_timeout_respect_fails_when_timeout_alarm_exists():
    config = load_guardrails("guardrails.yaml")
    artifact = _artifact(alarms=[{"type": "SESSION_TIMEOUT"}])

    result = _by_name(evaluate_checkpoints(artifact, config))["timeout_respect"]

    assert result.passed is False
    assert result.details["timeout_alarm_count"] == 1
