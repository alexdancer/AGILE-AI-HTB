"""Behavioral evals for the Estimator LLM.

Proves the estimator returns structured output, tracks usage as
estimation tokens, and fails into Blocked tasks without heuristic fallback.
"""

import json
import re
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
from agile_ai_htb.task_breakdown import (
    TaskBreakdownResult,
    TaskBreakdownValidationError,
    breakdown_task_source,
    validate_breakdown_result,
)

ROOT = Path(__file__).resolve().parents[2]
PORTAL_TOKEN = "test-portal-token"

MARKDOWN_EVAL_FIXTURES = {
    "repo_aware": """# DEMO_TASK_2099 repo-aware estimator input

Repository: DEMO_REPO_2099_TOKEN_TRACKER
Date: 2099-04-01

- [ ] Add DEMO_ROUTE_2099_budget_alarm fixture coverage
- [ ] Update DEMO_TEMPLATE_2099_session_report visibility
""".strip(),
    "phased": """# DEMO_TASK_2099 phased markdown task

- [ ] Phase DEMO_PHASE_2099_A: parse markdown intake
- [ ] Phase DEMO_PHASE_2099_B: decompose checklist tasks
- [ ] Phase DEMO_PHASE_2099_C: verify budget dashboard copy
""".strip(),
    "complex_rejection": """# DEMO_TASK_2099 complex manual estimate case

Need to rewrite DEMO_SYSTEM_2099_UNKNOWN with missing acceptance criteria by 2099-05-01.
""".strip(),
}


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




class FakeSequentialLLM:
    def __init__(self, contents):
        self.contents = list(contents)
        self.requests = []
        self.usage = {"prompt_tokens": 111, "completion_tokens": 22, "total_tokens": 133}

    async def acompletion(self, request):
        self.requests.append(request)
        if not self.contents:
            raise AssertionError("unexpected LLM request")
        return {
            "choices": [{"message": {"content": json.dumps(self.contents.pop(0))}}],
            "usage": self.usage,
        }


def _breakdown_content(*titles):
    return {
        "decision": "proposed_task_breakdown" if len(titles) > 1 else "single_task",
        "candidates": [
            {
                "kind": "implementation",
                "title": title,
                "prompt": f"Implement {title}",
                "acceptance_criteria": f"{title} has tests.",
                "constraints": [],
                "human_in_loop": True,
            }
            for title in titles
        ],
        "rejected_items": [
            {"text": "Date: 2099-04-01", "reason": "context metadata, not a task"}
        ],
        "global_contract_summary": "Accepted slices must collectively preserve DEMO_TASK_2099 output invariants.",
        "global_constraints": ["Do not add network dependencies."],
        "verification": ["Run pytest."],
        "non_goals": [],
        "recommended_sequence": list(titles),
        "confidence": 0.88,
        "rationale": "Task candidates are vertical slices derived from Markdown evidence.",
        "source": "llm",
    }


def _client_with_llm(tmp_path, llm):
    settings = Settings(
        database_path=tmp_path / "harness.db",
        guardrails_path=ROOT / "guardrails.yaml",
        estimator_model="openai/gpt-4.1-mini",
        task_breakdown_model="openai/gpt-4.1-mini",
        operator_config={},
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


@pytest.mark.asyncio
async def test_eval_task_breakdown_accepts_common_model_json_variants():
    """Task Breakdown Agent tolerates harmless JSON-shape drift from real models."""
    llm = FakeSequentialLLM(
        [
            {
                "decision": "single_task",
                "candidates": [
                    {
                        "kind": "implementation",
                        "title": "Run DEMO_2099 comparison",
                        "prompt": "Run the comparison demo from the uploaded Markdown.",
                        "acceptance_criteria": ["Portal shows reviewed candidate.", "pytest passes."],
                        "constraints": "Do not add network dependencies.",
                        "human_in_loop": True,
                    }
                ],
                "rejected_items": [],
                "global_contract_summary": "The DEMO_2099 comparison must stay synthetic and verified.",
                "global_constraints": [],
                "verification": ["Run pytest."],
                "non_goals": [],
                "recommended_sequence": ["Run DEMO_2099 comparison"],
                "confidence": 0.84,
                "rationale": "The uploaded Markdown describes one vertical slice.",
                "source": "llm",
                "notes": "Harmless extra provider/model field.",
            }
        ]
    )

    result, _ = await breakdown_task_source(
        "# DEMO_TASK_2099 comparison\n\n- [ ] Run comparison\n- [ ] Run pytest.",
        llm_client=llm,
        task_breakdown_model="gpt-5.4-mini",
    )

    assert isinstance(result, TaskBreakdownResult)
    assert result.global_contract_summary == "The DEMO_2099 comparison must stay synthetic and verified."
    assert result.candidates[0].kind == "implementation"
    assert result.candidates[0].acceptance_criteria == "Portal shows reviewed candidate.\npytest passes."
    assert result.candidates[0].constraints == ["Do not add network dependencies."]


def test_task_breakdown_candidate_kind_defaults_for_legacy_records():
    result = validate_breakdown_result(
        {
            "decision": "single_task",
            "candidates": [
                {
                    "title": "DEMO_TASK_2099 legacy candidate",
                    "prompt": "Implement the legacy DEMO candidate.",
                    "acceptance_criteria": "Tests pass.",
                    "constraints": [],
                    "human_in_loop": True,
                }
            ],
            "rejected_items": [],
            "global_contract_summary": "Legacy breakdown summary.",
            "global_constraints": [],
            "verification": [],
            "non_goals": [],
            "recommended_sequence": ["DEMO_TASK_2099 legacy candidate"],
            "confidence": 0.8,
            "rationale": "Legacy records did not store kind.",
            "source": "llm",
        }
    )

    assert result.candidates[0].kind == "implementation"


def test_task_breakdown_rejects_invalid_candidate_kind():
    with pytest.raises(TaskBreakdownValidationError, match="candidate kind"):
        validate_breakdown_result(
            {
                "decision": "single_task",
                "candidates": [
                    {
                        "kind": "whole_task_rerun",
                        "title": "DEMO_TASK_2099 invalid candidate",
                        "prompt": "Do the DEMO task.",
                        "acceptance_criteria": "Tests pass.",
                        "constraints": [],
                        "human_in_loop": True,
                    }
                ],
                "rejected_items": [],
                "global_contract_summary": "Invalid candidate summary.",
                "global_constraints": [],
                "verification": [],
                "non_goals": [],
                "recommended_sequence": ["DEMO_TASK_2099 invalid candidate"],
                "confidence": 0.8,
                "rationale": "Invalid kind must fail.",
                "source": "llm",
            }
        )


def test_estimate_form_failed_breakdown_records_validation_reason(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeSequentialLLM([{"not": "a valid breakdown"}])

    with _client_with_llm(tmp_path, llm) as client:
        response = client.post(
            "/tasks/estimate-form",
            headers={**_auth_headers(), "accept": "text/html"},
            data={"description": "# DEMO_TASK_2099 invalid output\n\n- [ ] Run comparison"},
            follow_redirects=False,
        )
        breakdown_id = response.headers["location"].split("/")[2]
        breakdown = db.get_task_breakdown(tmp_path / "harness.db", breakdown_id)

    assert response.status_code == 303
    assert breakdown["status"] == "failed"
    assert breakdown["failure_type"] == "TaskBreakdownValidationError"
    assert "task breakdown missing fields" in breakdown["failure_message"]


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


# ---------------------------------------------------------------------------
# Markdown task intake / decomposition behavior
# ---------------------------------------------------------------------------

def test_eval_repo_aware_markdown_intake_records_breakdown_review_and_model_usage(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeSequentialLLM([
        _breakdown_content(
            "Add DEMO_ROUTE_2099_budget_alarm fixture coverage",
            "Update DEMO_TEMPLATE_2099_session_report visibility",
        )
    ])
    client = _client_with_llm(tmp_path, llm)
    with client:
        response = client.post(
            "/tasks/estimate-form",
            data={"description": MARKDOWN_EVAL_FIXTURES["repo_aware"]},
            headers={**_auth_headers(), "accept": "text/html"},
            follow_redirects=False,
        )
        tasks = db.list_tasks(tmp_path / "harness.db")
        breakdown_id = response.headers["location"].split("/")[2]
        breakdown = db.get_task_breakdown(tmp_path / "harness.db", breakdown_id)
        usage = db.token_usage_breakdown(tmp_path / "harness.db")

    assert response.status_code == 303
    assert response.headers["location"].startswith("/task-breakdowns/")
    assert tasks == []
    assert breakdown["status"] == "proposed"
    assert breakdown["model"] == "openai/gpt-4.1-mini"
    assert breakdown["intake_metadata"]["intake_source"] == "markdown_paste"
    assert [candidate["title"] for candidate in breakdown["candidates"]] == [
        "Add DEMO_ROUTE_2099_budget_alarm fixture coverage",
        "Update DEMO_TEMPLATE_2099_session_report visibility",
    ]
    assert breakdown["rejected_items"][0]["reason"] == "context metadata, not a task"
    assert usage["by_category"]["task_breakdown"] == 133


def test_eval_bullet_markdown_direct_estimate_does_not_create_deterministic_breakdown_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM()
    client = _client_with_llm(tmp_path, llm)
    with client:
        response = client.post(
            "/estimate",
            json={"description": MARKDOWN_EVAL_FIXTURES["phased"]},
            headers=_auth_headers(),
        )

    task = response.json()
    assert response.status_code == 200
    assert task["status"] == "Estimated"
    assert "task_breakdown" not in task["metadata"]
    assert "decomposition_source" not in task["metadata"]


def test_eval_complex_markdown_failure_has_specific_manual_estimate_reason(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM(content={"complexity": "unknown", "source": "llm"})
    client = _client_with_llm(tmp_path, llm)
    with client:
        response = client.post(
            "/estimate",
            json={"description": MARKDOWN_EVAL_FIXTURES["complex_rejection"]},
            headers=_auth_headers(),
        )

    task = response.json()
    assert response.status_code == 200
    assert task["status"] == "Blocked"
    assert task["metadata"]["blocked_reason"] == "Estimator unavailable or invalid; manual estimate required."
    assert task["metadata"]["estimator_failure_type"] == "EstimatorValidationError"
    assert task["metadata"]["requires_manual_estimate"] is True


class EstimatorMarkdownFakeDataInvariantTests:
    """Markdown estimator fixtures must stay obviously synthetic."""

    __test__ = True

    def test_markdown_eval_fixture_values_are_demo_synthetic(self) -> None:
        text = "\n".join(MARKDOWN_EVAL_FIXTURES.values())
        assert "DEMO" in text
        assert "2099" in text
        real_years = re.findall(r"\b20(?:2[0-8])\b", text)
        assert real_years == []
        suspicious_values = [
            value for value in re.findall(r"\b[A-Z][A-Za-z0-9_-]*_\d{4}[A-Za-z0-9_-]*\b", text) if "DEMO" not in value
        ]
        assert suspicious_values == []
