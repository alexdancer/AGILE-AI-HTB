from dataclasses import replace
from pathlib import Path

from agile_ai_htb.governance import apply_governance
from agile_ai_htb.guardrails import load_guardrails


ROOT = Path(__file__).resolve().parents[1]


def _tool(name: str) -> dict:
    return {"type": "function", "function": {"name": name, "description": f"{name} tool"}}


def test_green_governance_rewrites_prompt_without_restricting_tools_or_increasing_max_tokens():
    config = load_guardrails(ROOT / "guardrails.yaml")
    request = {
        "model": "claude-haiku",
        "messages": [
            {"role": "system", "content": "original prompt"},
            {"role": "user", "content": "do the work"},
        ],
        "max_tokens": 1000,
        "tools": [_tool("web_search"), _tool("terminal")],
    }

    decision = apply_governance(request, "green", config)

    assert decision.request["messages"][0] == {
        "role": "system",
        "content": config.zones.system_prompt["green"],
    }
    assert decision.request["messages"][1:] == [{"role": "user", "content": "do the work"}]
    assert decision.request["max_tokens"] == 1000
    assert [tool["function"]["name"] for tool in decision.request["tools"]] == ["web_search", "terminal"]
    assert decision.zone == "green"
    assert decision.blocked_tools == []
    assert decision.max_tokens == 1000


def test_yellow_governance_prepends_prompt_clamps_tokens_and_removes_blocked_tools():
    config = load_guardrails(ROOT / "guardrails.yaml")
    request = {
        "model": "claude-sonnet",
        "messages": [{"role": "user", "content": "do the work"}],
        "max_tokens": 4096,
        "tools": [_tool("web_search"), _tool("browser_navigate"), _tool("read_file"), _tool("terminal")],
    }

    decision = apply_governance(request, "yellow", config)

    assert decision.request["messages"][0]["role"] == "system"
    assert decision.request["messages"][0]["content"] == config.zones.system_prompt["yellow"]
    assert decision.request["max_tokens"] == 2048
    assert [tool["function"]["name"] for tool in decision.request["tools"]] == ["read_file", "terminal"]
    assert decision.blocked_tools == ["web_search", "browser_navigate"]
    assert decision.max_tokens == 2048


def test_red_governance_keeps_only_tools_not_blocked_by_red_zone():
    config = load_guardrails(ROOT / "guardrails.yaml")
    request = {
        "model": "claude-opus",
        "messages": [{"role": "user", "content": "ship it"}],
        "tools": [
            _tool("web_search"),
            _tool("execute_code"),
            _tool("read_file"),
            _tool("patch"),
            _tool("terminal"),
        ],
    }

    decision = apply_governance(request, "red", config)

    assert decision.request["messages"][0]["content"] == config.zones.system_prompt["red"]
    assert decision.request["max_tokens"] == 1024
    assert [tool["function"]["name"] for tool in decision.request["tools"]] == ["read_file", "patch", "terminal"]
    assert decision.blocked_tools == ["web_search", "execute_code"]


def test_red_governance_removes_unlisted_non_delivery_tools_and_does_not_mutate_input():
    config = load_guardrails(ROOT / "guardrails.yaml")
    request = {
        "model": "claude-opus",
        "messages": [{"role": "user", "content": "ship it"}],
        "max_tokens": 4096,
        "tools": [
            {"name": "read_file"},
            {"name": "write_file"},
            {"name": "process"},
            {"name": "terminal"},
        ],
    }

    decision = apply_governance(request, "red", config)

    assert request["messages"] == [{"role": "user", "content": "ship it"}]
    assert request["max_tokens"] == 4096
    assert [tool["name"] for tool in request["tools"]] == ["read_file", "write_file", "process", "terminal"]
    assert [tool["name"] for tool in decision.request["tools"]] == ["read_file", "terminal"]
    assert decision.blocked_tools == ["write_file", "process"]


def test_disabled_zones_leave_request_unchanged():
    config = load_guardrails(ROOT / "guardrails.yaml")
    disabled = replace(config, zones=replace(config.zones, enabled=False))
    request = {
        "model": "claude-sonnet",
        "messages": [{"role": "user", "content": "do the work"}],
        "max_tokens": 4096,
        "tools": [_tool("web_search")],
    }

    decision = apply_governance(request, "red", disabled)

    assert decision.request == request
    assert decision.blocked_tools == []
    assert decision.max_tokens == 4096


def test_malformed_tools_are_removed_without_none_in_blocked_tools():
    config = load_guardrails(ROOT / "guardrails.yaml")
    request = {
        "model": "claude-opus",
        "messages": [{"role": "user", "content": "ship it"}],
        "tools": [{"type": "function", "function": {}}, {"metadata": "missing name"}, _tool("terminal")],
    }

    decision = apply_governance(request, "red", config)

    assert [tool["function"]["name"] for tool in decision.request["tools"]] == ["terminal"]
    assert decision.blocked_tools == ["<unnamed>", "<unnamed>"]
