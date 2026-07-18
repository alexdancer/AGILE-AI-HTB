"""Behavioral evals for proxy token tracking fidelity.

Proves the harness proxy records prompt/completion/total tokens with
correct usage_kind through the full proxy request path.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from foreman_ai_hq import db
from foreman_ai_hq.app import create_app
from foreman_ai_hq.settings import Settings

ROOT = Path(__file__).resolve().parents[2]


class FakeLLMClient:
    def __init__(self):
        self.requests = []

    async def acompletion(self, request):
        self.requests.append(request)
        return {
            "id": "chatcmpl_fake",
            "object": "chat.completion",
            "model": request["model"],
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "done"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 600, "completion_tokens": 500, "total_tokens": 1100},
        }


def _client(tmp_path):
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    app = create_app(settings)
    fake = FakeLLMClient()
    app.state.llm_client = fake
    return TestClient(app), fake


def _start_session(client, **budget_kw):
    budget = {"daily_used_tokens": 0, "daily_cap_tokens": 1_000_000, "session_cap_tokens": 200_000, **budget_kw}
    return client.post(
        "/session/start",
        headers={"Authorization": "Bearer test-portal-token"},
        json={"task_description": "Proxy token tracking", "model": "claude-haiku", "budget": budget},
    ).json()


def _proxy_request(client, session_api_key, model="claude-haiku"):
    return client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {session_api_key}"},
        json={"model": model, "messages": [{"role": "user", "content": "finish"}]},
    )


def test_eval_proxy_token_turn_has_usage_kind_worker(tmp_path):
    """Single proxy request records a token_turn with usage_kind='worker'."""
    client, fake = _client(tmp_path)
    with client:
        started = _start_session(client)
        response = _proxy_request(client, started["session_api_key"])

    assert response.status_code == 200
    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    assert len(artifact["token_log"]) == 1
    assert artifact["token_log"][0]["usage_kind"] == "worker"


def test_eval_proxy_token_turn_matches_fake_llm_usage(tmp_path):
    """Token totals in artifact match the fake LLM usage response exactly."""
    client, fake = _client(tmp_path)
    with client:
        started = _start_session(client)
        _proxy_request(client, started["session_api_key"])

    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    log = artifact["token_log"][0]
    assert log["prompt_tokens"] == 600
    assert log["completion_tokens"] == 500
    assert log["total_tokens"] == 1100


def test_eval_proxy_multiple_turns_accumulate_in_artifact(tmp_path):
    """Three proxy requests produce three token_log entries in order."""
    client, fake = _client(tmp_path)
    with client:
        started = _start_session(client)
        for _ in range(3):
            _proxy_request(client, started["session_api_key"])

    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    assert len(artifact["token_log"]) == 3
    for entry in artifact["token_log"]:
        assert entry["usage_kind"] == "worker"
        assert entry["total_tokens"] == 1100


def test_eval_proxy_token_turn_records_null_for_unpriced_model(tmp_path):
    """Unpriced proxy usage stays distinguishable from a genuinely free call."""
    client, fake = _client(tmp_path)
    with client:
        started = _start_session(client)
        _proxy_request(client, started["session_api_key"])

    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    log = artifact["token_log"][0]
    assert "cost" in log
    assert log["cost"] is None


def test_eval_proxy_usage_kind_persisted_in_db_row(tmp_path):
    """usage_kind='worker' is persisted in the raw database row, not just artifact."""
    client, fake = _client(tmp_path)
    with client:
        started = _start_session(client)
        _proxy_request(client, started["session_api_key"])

    with db.connect(tmp_path / "harness.db") as conn:
        row = conn.execute(
            "select usage_kind, prompt_tokens, completion_tokens, total_tokens from token_turns"
        ).fetchone()

    assert row["usage_kind"] == "worker"
    assert row["prompt_tokens"] == 600
    assert row["completion_tokens"] == 500
    assert row["total_tokens"] == 1100
