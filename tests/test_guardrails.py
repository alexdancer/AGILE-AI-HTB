from pathlib import Path
from dataclasses import replace

import pytest

from agile_ai_htb.guardrails import get_budget_zone, load_guardrails


ROOT = Path(__file__).resolve().parents[1]


def test_load_guardrails_preserves_real_yaml_configuration():
    config = load_guardrails(ROOT / "guardrails.yaml")

    assert config.daily_cap.tokens == 1_000_000
    assert config.daily_cap.budget_period == "daily"
    assert config.session_cap.tokens == 200_000
    assert config.zones.green == 0.60
    assert config.zones.yellow == 0.85
    assert config.zones.red == 1.0
    assert config.zones.system_prompt["yellow"].startswith("Budget is limited")
    assert config.zones.max_tokens == {"green": 4096, "yellow": 2048, "red": 1024}
    assert "web_search" in config.zones.blocked_tools["yellow"]
    assert "execute_code" in config.zones.blocked_tools["red"]
    assert config.loop_detection.threshold == 5
    assert config.session_timeout.duration == 1800
    assert config.tool_category_limit.limit == 0.50
    assert config.tool_categories["delegation"].weight == 1.5
    assert config.notifications.macos_notification is True
    assert config.model_routing.task_complexity["complex"].recommended_model == "claude-3-opus-20240229"
    assert config.model_routing.budget_aware_clamp.remaining_daily_threshold == 0.15


def test_load_guardrails_rejects_invalid_zone_order(tmp_path):
    invalid = tmp_path / "guardrails.yaml"
    invalid.write_text(
        """
guardrails:
  daily_cap: {enabled: true, tokens: 100, budget_period: daily, reset_time: '00:00', action: notify}
  session_cap: {enabled: true, tokens: 50, action: notify}
  zones:
    enabled: true
    green: 0.90
    yellow: 0.85
    red: 1.0
    enforcement:
      system_prompt: {green: green, yellow: yellow, red: red}
      max_tokens: {green: 4096, yellow: 2048, red: 1024}
      blocked_tools: {yellow: [], red: []}
  loop_detection: {enabled: true, threshold: 5, action: notify}
  session_timeout: {enabled: true, duration: 1800, action: notify_and_checkpoint}
  tool_category_limit: {enabled: true, limit: 0.5, action: inject_context}
tool_categories: {}
notifications: {discord_webhook: '', slack_webhook: '', macos_notification: true}
model_routing:
  task_complexity: {}
  budget_aware_clamp: {enabled: true, remaining_daily_threshold: 0.15, note: note}
"""
    )

    with pytest.raises(ValueError, match="zone thresholds"):
        load_guardrails(invalid)


@pytest.mark.parametrize(
    ("used_tokens", "daily_cap", "expected_zone"),
    [
        (0, 1_000_000, "green"),
        (599_999, 1_000_000, "green"),
        (600_000, 1_000_000, "yellow"),
        (849_999, 1_000_000, "yellow"),
        (850_000, 1_000_000, "red"),
        (1_200_000, 1_000_000, "red"),
        (100_000, 0, "green"),
        (100_000, None, "green"),
    ],
)
def test_get_budget_zone_uses_configured_boundaries(used_tokens, daily_cap, expected_zone):
    config = load_guardrails(ROOT / "guardrails.yaml")

    assert get_budget_zone(used_tokens, daily_cap, config) == expected_zone


def test_get_budget_zone_stays_green_when_zones_disabled():
    config = load_guardrails(ROOT / "guardrails.yaml")
    disabled = replace(config, zones=replace(config.zones, enabled=False))

    assert get_budget_zone(900_000, 1_000_000, disabled) == "green"
