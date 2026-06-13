"""Behavioral evals for budget zone transitions.

Proves sequential sessions push daily budget from green→yellow→red
and that governance layers fire at the correct boundaries.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


class FakeZoneLLMClient:
    def __init__(self):
        self.requests = []

    async def acompletion(self, request):
        self.requests.append(request)
        return {
            "id": "chatcmpl_fake",
            "object": "chat.completion",
            "model": request["model"],
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "done"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300},
        }


def _client(tmp_path):
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    app = create_app(settings)
    fake = FakeZoneLLMClient()
    app.state.llm_client = fake
    return TestClient(app), fake


def _start_session(client, daily_used_tokens, daily_cap_tokens=1_000_000):
    return client.post(
        "/session/start",
        json={
            "task_description": "Zone transition test",
            "model": "claude-haiku",
            "budget": {"daily_used_tokens": daily_used_tokens, "daily_cap_tokens": daily_cap_tokens},
        },
    ).json()


def _proxy_request(client, session_api_key, tools=None):
    payload = {"model": "claude-haiku", "messages": [{"role": "user", "content": "finish"}]}
    if tools:
        payload["tools"] = tools
    return client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {session_api_key}"},
        json=payload,
    )


def _tool(name):
    return {"type": "function", "function": {"name": name}}


# ---------------------------------------------------------------------------
# Green zone (0% budget)
# ---------------------------------------------------------------------------

def test_eval_green_zone_full_tools_full_max_tokens(tmp_path):
    """At 0% daily budget, all tools present, max_tokens unchanged, green prompt."""
    client, fake = _client(tmp_path)
    with client:
        started = _start_session(client, daily_used_tokens=0)
        assert started["starting_zone"] == "green"

        response = _proxy_request(
            client,
            started["session_api_key"],
            tools=[_tool("web_search"), _tool("read_file"), _tool("terminal")],
        )

    assert response.status_code == 200
    forwarded = fake.requests[0]
    assert forwarded["messages"][0]["content"].startswith("You have ample token budget")
    # max_tokens not clamped in green
    assert "max_tokens" not in forwarded or forwarded.get("max_tokens", 4096) >= 4096
    names = [t["function"]["name"] for t in forwarded["tools"]]
    assert "web_search" in names
    assert "terminal" in names

    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    assert artifact["guardrail_snapshots"][0]["zone"] == "green"


# ---------------------------------------------------------------------------
# Yellow zone (60% budget)
# ---------------------------------------------------------------------------

def test_eval_yellow_zone_clamps_max_tokens_and_blocks_tools(tmp_path):
    """At 60% daily budget, governance clamps max_tokens, blocks web tools, rewrites prompt."""
    client, fake = _client(tmp_path)
    with client:
        started = _start_session(client, daily_used_tokens=600_000)  # exactly 60%
        assert started["starting_zone"] == "yellow"

        response = _proxy_request(
            client,
            started["session_api_key"],
            tools=[_tool("web_search"), _tool("browser_navigate"), _tool("read_file"), _tool("terminal")],
        )

    assert response.status_code == 200
    forwarded = fake.requests[0]
    assert forwarded["messages"][0]["content"].startswith("Budget is limited")
    assert forwarded["max_tokens"] == 2048
    names = [t["function"]["name"] for t in forwarded["tools"]]
    assert "web_search" not in names
    assert "browser_navigate" not in names
    assert "read_file" in names
    assert "terminal" in names

    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    snapshot = artifact["guardrail_snapshots"][0]
    assert snapshot["zone"] == "yellow"
    assert "web_search" in snapshot["decision"]["blocked_tools"]


# ---------------------------------------------------------------------------
# Red zone (85% budget)
# ---------------------------------------------------------------------------

def test_eval_red_zone_delivery_only_tools_and_max_tokens(tmp_path):
    """At 85% daily budget, only read_file/patch/terminal remain, max_tokens at 1024."""
    client, fake = _client(tmp_path)
    with client:
        started = _start_session(client, daily_used_tokens=850_000)  # exactly 85%
        assert started["starting_zone"] == "red"

        response = _proxy_request(
            client,
            started["session_api_key"],
            tools=[
                _tool("web_search"),
                _tool("execute_code"),
                _tool("read_file"),
                _tool("patch"),
                _tool("terminal"),
            ],
        )

    assert response.status_code == 200
    forwarded = fake.requests[0]
    assert forwarded["messages"][0]["content"].startswith("Budget critical")
    assert forwarded["max_tokens"] == 1024
    names = [t["function"]["name"] for t in forwarded["tools"]]
    assert "web_search" not in names
    assert "execute_code" not in names
    assert names == ["read_file", "patch", "terminal"]

    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    snapshot = artifact["guardrail_snapshots"][0]
    assert snapshot["zone"] == "red"
    assert snapshot["decision"]["max_tokens"] == 1024


# ---------------------------------------------------------------------------
# Zone boundary precision
# ---------------------------------------------------------------------------

def test_eval_zone_boundary_green_to_yellow_at_60_percent(tmp_path):
    """Zone switches at exactly 60% (599,999 = green, 600,000 = yellow)."""
    client, fake = _client(tmp_path)
    with client:
        # Just below 60%
        started_green = _start_session(client, daily_used_tokens=599_999, daily_cap_tokens=1_000_000)
        assert started_green["starting_zone"] == "green"

        # Exactly at 60%
        started_yellow = _start_session(client, daily_used_tokens=600_000, daily_cap_tokens=1_000_000)
        assert started_yellow["starting_zone"] == "yellow"


def test_eval_zone_boundary_yellow_to_red_at_85_percent(tmp_path):
    """Zone switches at exactly 85% (849,999 = yellow, 850,000 = red)."""
    client, fake = _client(tmp_path)
    with client:
        # Just below 85%
        started_yellow = _start_session(client, daily_used_tokens=849_999, daily_cap_tokens=1_000_000)
        assert started_yellow["starting_zone"] == "yellow"

        # Exactly at 85%
        started_red = _start_session(client, daily_used_tokens=850_000, daily_cap_tokens=1_000_000)
        assert started_red["starting_zone"] == "red"


def test_eval_over_cap_stays_red(tmp_path):
    """Over 100% daily budget stays red (does not crash or return green)."""
    client, fake = _client(tmp_path)
    with client:
        started = _start_session(client, daily_used_tokens=1_200_000, daily_cap_tokens=1_000_000)
        assert started["starting_zone"] == "red"
