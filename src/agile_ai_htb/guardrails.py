from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

BudgetZone = Literal["green", "yellow", "red"]


@dataclass(frozen=True)
class DailyCapConfig:
    enabled: bool
    budget_period: str
    tokens: int
    reset_time: str
    action: str


@dataclass(frozen=True)
class SessionCapConfig:
    enabled: bool
    tokens: int
    action: str


@dataclass(frozen=True)
class ZoneConfig:
    enabled: bool
    green: float
    yellow: float
    red: float
    system_prompt: dict[str, str]
    max_tokens: dict[str, int]
    blocked_tools: dict[str, list[str]]


@dataclass(frozen=True)
class LoopDetectionConfig:
    enabled: bool
    threshold: int
    action: str


@dataclass(frozen=True)
class SessionTimeoutConfig:
    enabled: bool
    duration: int
    action: str


@dataclass(frozen=True)
class ToolCategoryLimitConfig:
    enabled: bool
    limit: float
    action: str


@dataclass(frozen=True)
class ToolCategoryConfig:
    weight: float


@dataclass(frozen=True)
class NotificationConfig:
    discord_webhook: str
    slack_webhook: str
    macos_notification: bool


@dataclass(frozen=True)
class TaskComplexityConfig:
    description: str
    recommended_model: str


@dataclass(frozen=True)
class BudgetAwareClampConfig:
    enabled: bool
    remaining_daily_threshold: float
    note: str


@dataclass(frozen=True)
class ModelRoutingConfig:
    task_complexity: dict[str, TaskComplexityConfig]
    budget_aware_clamp: BudgetAwareClampConfig


@dataclass(frozen=True)
class GuardrailConfig:
    daily_cap: DailyCapConfig
    session_cap: SessionCapConfig
    zones: ZoneConfig
    loop_detection: LoopDetectionConfig
    session_timeout: SessionTimeoutConfig
    tool_category_limit: ToolCategoryLimitConfig
    tool_categories: dict[str, ToolCategoryConfig]
    notifications: NotificationConfig
    model_routing: ModelRoutingConfig


def load_guardrails(path: Path | str) -> GuardrailConfig:
    data = yaml.safe_load(Path(path).read_text())
    guardrails = data["guardrails"]
    zones = guardrails["zones"]
    enforcement = zones["enforcement"]

    zone_config = ZoneConfig(
        enabled=bool(zones["enabled"]),
        green=float(zones["green"]),
        yellow=float(zones["yellow"]),
        red=float(zones["red"]),
        system_prompt=dict(enforcement["system_prompt"]),
        max_tokens={zone: int(tokens) for zone, tokens in enforcement["max_tokens"].items()},
        blocked_tools={zone: list(tools) for zone, tools in enforcement["blocked_tools"].items()},
    )
    if not zone_config.green < zone_config.yellow <= zone_config.red:
        raise ValueError("zone thresholds must satisfy green < yellow <= red")

    model_routing = data["model_routing"]
    budget_aware_clamp = model_routing["budget_aware_clamp"]

    return GuardrailConfig(
        daily_cap=DailyCapConfig(**guardrails["daily_cap"]),
        session_cap=SessionCapConfig(**guardrails["session_cap"]),
        zones=zone_config,
        loop_detection=LoopDetectionConfig(**guardrails["loop_detection"]),
        session_timeout=SessionTimeoutConfig(**guardrails["session_timeout"]),
        tool_category_limit=ToolCategoryLimitConfig(**guardrails["tool_category_limit"]),
        tool_categories={
            name: ToolCategoryConfig(weight=float(config["weight"]))
            for name, config in data.get("tool_categories", {}).items()
        },
        notifications=NotificationConfig(**data["notifications"]),
        model_routing=ModelRoutingConfig(
            task_complexity={
                name: TaskComplexityConfig(**config)
                for name, config in model_routing.get("task_complexity", {}).items()
            },
            budget_aware_clamp=BudgetAwareClampConfig(**budget_aware_clamp),
        ),
    )


def get_budget_zone(
    used_tokens: int,
    daily_cap: int | None,
    config: GuardrailConfig,
) -> BudgetZone:
    if not config.zones.enabled:
        return "green"
    if not daily_cap or daily_cap <= 0:
        return "green"

    usage_ratio = used_tokens / daily_cap
    # The yellow threshold is the red-zone trigger; the green threshold starts warning mode.
    if usage_ratio >= config.zones.yellow:
        return "red"
    if usage_ratio >= config.zones.green:
        return "yellow"
    return "green"
