from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from token_tracker_harness.guardrails import BudgetZone, GuardrailConfig

RED_ALLOWED_TOOL_NAMES = {"read_file", "patch", "terminal"}


@dataclass(frozen=True)
class GovernanceDecision:
    request: dict[str, Any]
    zone: BudgetZone
    blocked_tools: list[str]
    max_tokens: int


def apply_governance(
    request: dict[str, Any],
    zone: BudgetZone,
    config: GuardrailConfig,
) -> GovernanceDecision:
    governed_request = deepcopy(request)
    if not config.zones.enabled:
        return GovernanceDecision(
            request=governed_request,
            zone=zone,
            blocked_tools=[],
            max_tokens=int(governed_request.get("max_tokens", 0)),
        )

    governed_request["messages"] = _rewrite_system_prompt(
        governed_request.get("messages", []),
        config.zones.system_prompt[zone],
    )
    governed_request["max_tokens"] = _clamp_max_tokens(
        governed_request.get("max_tokens"),
        config.zones.max_tokens[zone],
    )
    governed_request["tools"], blocked_tools = _filter_tools(
        governed_request.get("tools", []),
        set(config.zones.blocked_tools.get(zone, [])),
        allowed_tool_names=RED_ALLOWED_TOOL_NAMES if zone == "red" else None,
    )

    return GovernanceDecision(
        request=governed_request,
        zone=zone,
        blocked_tools=blocked_tools,
        max_tokens=governed_request["max_tokens"],
    )


def _rewrite_system_prompt(messages: list[dict[str, Any]], zone_prompt: str) -> list[dict[str, Any]]:
    replacement = {"role": "system", "content": zone_prompt}
    if messages and messages[0].get("role") == "system":
        return [replacement, *messages[1:]]
    return [replacement, *messages]


def _clamp_max_tokens(requested_max_tokens: int | None, zone_max_tokens: int) -> int:
    if requested_max_tokens is None:
        return zone_max_tokens
    return min(int(requested_max_tokens), zone_max_tokens)


def _filter_tools(
    tools: list[dict[str, Any]],
    blocked_tool_names: set[str],
    allowed_tool_names: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    allowed_tools = []
    blocked_tools = []
    for tool in tools:
        name = _tool_name(tool)
        if name in blocked_tool_names or (
            allowed_tool_names is not None and name not in allowed_tool_names
        ):
            blocked_tools.append(name or "<unnamed>")
            continue
        allowed_tools.append(tool)
    return allowed_tools, blocked_tools


def _tool_name(tool: dict[str, Any]) -> str | None:
    if "function" in tool and isinstance(tool["function"], dict):
        return tool["function"].get("name")
    return tool.get("name")
