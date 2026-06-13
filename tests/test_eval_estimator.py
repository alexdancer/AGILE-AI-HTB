"""Behavioral evals for the Estimator LLM.

Proves the estimator returns structured output, tracks usage as
estimation tokens, and fails into Blocked tasks without heuristic fallback.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.estimation import (
    EstimatorUnavailableError,
    EstimatorValidationError,
    EstimateResult,
    estimate_task,
)
from agile_ai_htb.guardrails import load_guardrails
from agile_ai_htb.settings import Settings

ROOT = Path(__file__).resolve().parents[1]
PORTAL_TOKEN = "test-portal-token"


def _auth_headers():
    return {"Authorization": f"Bearer {PORTAL_TOKEN}"}


class FakeEstimatorLLM:
    """Fake LLM that returns structured estimate JSON or raises on command."""

    def __init__(self, *, content=None, exc=None, usage=None):
        self.content = content or {
            "token_estimate": 12_345,
            "complexity": "modest",
            "recommended_model": "claude-3-5-sonnet-20240620",
            "confidence": 0.82,
            "rationale": "Endpoint plus tests is a modest task.",
            "assumptions": ["No schema migration needed."],
            "risk_flags": ["Integration tests may expand scope"],
            "spike_recommendation": "No spike needed.",
            "budget_note": "Within normal daily budget.",
            "source": "llm",
        }
        self.exc = exc
        self.usage = usage or {"prompt_tokens": 111, "completion_tokens": 22, "total_tokens": 133}
        self.requests = []

    async def acompletion(self, request):
        self.requests.append(request)
        if self.exc:
            raise self.exc
        return {
            "choices": [{"message": {"content": json.dumps(self.content)}}],
            "usage": self.usage,
        }


def _client_with_llm(tmp_path, llm):
    settings = Settings(
        database_path=tmp_path / "harness.db",
        guardrails_path=ROOT / "guardrails.yaml",
        estimator_model="openai/gpt-4.1-mini",
    )
    app = create_app(settings)
    app.state.llm_client = llm
    return TestClient(app)


# ---------------------------------------------------------------------------
# Structured output
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_eval_estimator_returns_all_required_fields():
    """Estimator LLM response is parsed into EstimateResult with all 11 fields."""
    config = load_guardrails(ROOT / "guardrails.yaml")
    llm = FakeEstimatorLLM()
    result, response = await estimate_task(
        "Add a new REST endpoint with tests",
        config,
        llm_client=llm,
        estimator_model="gpt-4o-mini",
    )

    assert isinstance(result, EstimateResult)
    assert result.token_estimate == 12_345
    assert result.complexity == "modest"
    assert result.recommended_model == "claude-3-5-sonnet-20240620"
    assert result.confidence == 0.82
    assert result.rationale
    assert isinstance(result.assumptions, list)
    assert isinstance(result.risk_flags, list)
    assert result.spike_recommendation
    assert result.budget_note
    assert result.source == "llm"


@pytest.mark.asyncio
async def test_eval_estimator_as_dict_has_expected_keys():
    """EstimateResult.as_dict() returns all expected keys."""
    config = load_guardrails(ROOT / "guardrails.yaml")
    llm = FakeEstimatorLLM()
    result, _ = await estimate_task("Fix a typo", config, llm_client=llm, estimator_model="gpt-4o-mini")

    d = result.as_dict()
    assert set(d.keys()) == {
        "token_estimate", "complexity", "recommended_model", "confidence",
        "rationale", "assumptions", "risk_flags", "spike_recommendation",
        "budget_note", "source",
    }


@pytest.mark.asyncio
async def test_eval_estimator_token_estimate_is_positive_integer():
    """Token estimate must be a positive integer, not zero or negative."""
    config = load_guardrails(ROOT / "guardrails.yaml")
    llm = FakeEstimatorLLM(content={
        "token_estimate": 8_000,
        "complexity": "simple",
        "recommended_model": "claude-3-haiku-20240307",
        "confidence": 0.95,
        "rationale": "Trivial fix.",
        "assumptions": [],
        "risk_flags": [],
        "spike_recommendation": "",
        "budget_note": "",
        "source": "llm",
    })
    result, _ = await estimate_task("Fix a trailing comma", config, llm_client=llm, estimator_model="gpt-4o-mini")
    assert result.token_estimate == 8_000
    assert result.token_estimate > 0


# ---------------------------------------------------------------------------
# Estimation token tracking
# ---------------------------------------------------------------------------

def test_eval_estimator_usage_tracked_as_estimation_kind(tmp_path, monkeypatch):
    """Estimator token usage is persisted with usage_kind='estimation'."""
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM()
    client = _client_with_llm(tmp_path, llm)

    with client:
        response = client.post(
            "/estimate",
            json={"description": "Add a save command and test it"},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    assert response.json()["status"] == "Estimated"

    with db.connect(tmp_path / "harness.db") as conn:
        rows = conn.execute("select usage_kind from token_turns").fetchall()
    kinds = {row["usage_kind"] for row in rows}
    assert "estimation" in kinds


def test_eval_estimator_tokens_count_against_daily_budget(tmp_path, monkeypatch):
    """Estimator tokens are recorded in token_turns and accumulate toward daily total."""
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM()
    client = _client_with_llm(tmp_path, llm)

    with client:
        client.post(
            "/estimate",
            json={"description": "Add a list endpoint"},
            headers=_auth_headers(),
        )

    with db.connect(tmp_path / "harness.db") as conn:
        row = conn.execute(
            "select prompt_tokens, completion_tokens, total_tokens from token_turns where usage_kind = 'estimation'"
        ).fetchone()

    assert row["prompt_tokens"] == 111
    assert row["completion_tokens"] == 22
    assert row["total_tokens"] == 133


# ---------------------------------------------------------------------------
# Estimator failures → Blocked
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_eval_estimator_unavailable_raises_typed_error():
    """LLM call failure raises EstimatorUnavailableError, not a generic exception."""
    config = load_guardrails(ROOT / "guardrails.yaml")
    llm = FakeEstimatorLLM(exc=RuntimeError("connection refused"))

    with pytest.raises(EstimatorUnavailableError, match="connection refused"):
        await estimate_task("Task", config, llm_client=llm, estimator_model="gpt-4o-mini")


@pytest.mark.asyncio
async def test_eval_estimator_invalid_json_raises_validation_error():
    """Non-JSON response raises EstimatorValidationError."""
    config = load_guardrails(ROOT / "guardrails.yaml")
    llm = FakeEstimatorLLM(content="not valid json")  # string, not dict

    with pytest.raises(EstimatorValidationError, match="estimator JSON must be an object"):
        await estimate_task("Task", config, llm_client=llm, estimator_model="gpt-4o-mini")


def test_eval_estimator_failure_creates_blocked_task(tmp_path, monkeypatch):
    """When estimator fails, the task endpoint returns Blocked, not Estimated."""
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM(exc=RuntimeError("provider down"))
    client = _client_with_llm(tmp_path, llm)

    with client:
        response = client.post(
            "/estimate",
            json={"description": "Add export endpoint"},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Blocked"
    assert "estimator_unavailable" in body.get("metadata", {}).get("blocked_reason", "") or "Estimator unavailable" in body.get("metadata", {}).get("blocked_reason", "")
