"""Behavioral evals for alarm firing.

Proves all 7 alarm types fire under correct conditions with
correct severity through the proxy integration path.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.alarms import (
    alarm_for_checkpoint_failure,
    detect_budget_alarms,
    detect_loop,
    detect_session_timeout,
    detect_tool_category_bias,
)
from agile_ai_htb.app import create_app
from agile_ai_htb.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


class FakeAlarmLLMClient:
    def __init__(self):
        self.requests = []

    async def acompletion(self, request):
        self.requests.append(request)
        return {
            "id": "chatcmpl_fake",
            "object": "chat.completion",
            "model": request["model"],
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "done"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 500, "completion_tokens": 200, "total_tokens": 700},
        }


def _client(tmp_path):
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    app = create_app(settings)
    app.state.llm_client = FakeAlarmLLMClient()
    return TestClient(app)


def _start_session(client, daily_used_tokens=0, daily_cap_tokens=1_000_000, session_cap_tokens=200_000):
    return client.post(
        "/session/start",
        json={
            "task_description": "Alarm eval",
            "model": "claude-haiku",
            "budget": {
                "daily_used_tokens": daily_used_tokens,
                "daily_cap_tokens": daily_cap_tokens,
                "session_cap_tokens": session_cap_tokens,
            },
        },
    ).json()


def _proxy_request(client, session_api_key):
    return client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {session_api_key}"},
        json={"model": "claude-haiku", "messages": [{"role": "user", "content": "finish"}]},
    )


# ---------------------------------------------------------------------------
# BUDGET_YELLOW
# ---------------------------------------------------------------------------

def test_eval_alarm_budget_yellow_fires_in_yellow_zone(tmp_path):
    """BUDGET_YELLOW alarm (LOW) fires when daily budget enters yellow zone."""
    client = _client(tmp_path)
    with client:
        started = _start_session(client, daily_used_tokens=650_000)
        _proxy_request(client, started["session_api_key"])

    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    alarm_types = {a["type"] for a in artifact["alarms"]}
    assert "BUDGET_YELLOW" in alarm_types
    yellow_alarm = next(a for a in artifact["alarms"] if a["type"] == "BUDGET_YELLOW")
    assert yellow_alarm["severity"] == "LOW"
    assert yellow_alarm["context"]["zone"] == "yellow"


# ---------------------------------------------------------------------------
# BUDGET_RED
# ---------------------------------------------------------------------------

def test_eval_alarm_budget_red_fires_in_red_zone(tmp_path):
    """BUDGET_RED alarm (MEDIUM) fires when daily budget enters red zone."""
    client = _client(tmp_path)
    with client:
        started = _start_session(client, daily_used_tokens=900_000)
        _proxy_request(client, started["session_api_key"])

    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    alarm_types = {a["type"] for a in artifact["alarms"]}
    assert "BUDGET_RED" in alarm_types
    red_alarm = next(a for a in artifact["alarms"] if a["type"] == "BUDGET_RED")
    assert red_alarm["severity"] == "MEDIUM"
    assert red_alarm["context"]["zone"] == "red"


# ---------------------------------------------------------------------------
# DAILY_CAP_EXCEEDED
# ---------------------------------------------------------------------------

def test_eval_alarm_daily_cap_exceeded_fires_when_cap_crossed(tmp_path):
    """DAILY_CAP_EXCEEDED alarm (HIGH) fires when daily usage exceeds the cap."""
    client = _client(tmp_path)
    with client:
        started = _start_session(client, daily_used_tokens=1_100_000, daily_cap_tokens=1_000_000)
        _proxy_request(client, started["session_api_key"])

    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    alarm_types = {a["type"] for a in artifact["alarms"]}
    assert "DAILY_CAP_EXCEEDED" in alarm_types
    cap_alarm = next(a for a in artifact["alarms"] if a["type"] == "DAILY_CAP_EXCEEDED")
    assert cap_alarm["severity"] == "HIGH"


# ---------------------------------------------------------------------------
# SESSION_CAP_EXCEEDED
# ---------------------------------------------------------------------------

def test_eval_alarm_session_cap_exceeded_fires_when_session_cap_crossed(tmp_path):
    """SESSION_CAP_EXCEEDED alarm (MEDIUM) fires when session tokens exceed cap."""
    client = _client(tmp_path)
    with client:
        started = _start_session(client, session_cap_tokens=500)
        # Two requests at 700 tokens each = 1,400 > 500 cap
        _proxy_request(client, started["session_api_key"])
        _proxy_request(client, started["session_api_key"])

    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    alarm_types = {a["type"] for a in artifact["alarms"]}
    assert "SESSION_CAP_EXCEEDED" in alarm_types
    sess_alarm = next(a for a in artifact["alarms"] if a["type"] == "SESSION_CAP_EXCEEDED")
    assert sess_alarm["severity"] == "MEDIUM"


# ---------------------------------------------------------------------------
# LOOP_DETECTED (unit-level — no proxy path for tool traces)
# ---------------------------------------------------------------------------

def test_eval_alarm_loop_detected_fires_with_repeated_tool_calls():
    """LOOP_DETECTED alarm (MEDIUM) fires after 5 consecutive identical tool+input calls."""
    trace = [
        {"tool_name": "read_file", "input_hash": "abc"},
        {"tool_name": "read_file", "input_hash": "abc"},
        {"tool_name": "read_file", "input_hash": "abc"},
        {"tool_name": "read_file", "input_hash": "abc"},
        {"tool_name": "read_file", "input_hash": "abc"},
    ]
    alarm = detect_loop(trace, threshold=5, session_id="sess-eval")
    assert alarm is not None
    assert alarm.type == "LOOP_DETECTED"
    assert alarm.severity == "MEDIUM"
    assert alarm.context["repetition_count"] == 5


def test_eval_alarm_loop_not_fired_below_threshold():
    """No LOOP_DETECTED alarm when identical calls are below threshold."""
    trace = [
        {"tool_name": "read_file", "input_hash": "abc"},
        {"tool_name": "read_file", "input_hash": "abc"},
        {"tool_name": "read_file", "input_hash": "abc"},
        {"tool_name": "read_file", "input_hash": "abc"},
    ]
    alarm = detect_loop(trace, threshold=5, session_id="sess-eval")
    assert alarm is None


# ---------------------------------------------------------------------------
# SESSION_TIMEOUT
# ---------------------------------------------------------------------------

def test_eval_alarm_session_timeout_fires_when_elapsed_exceeds_timeout():
    """SESSION_TIMEOUT alarm (MEDIUM) fires when wall clock exceeds timeout."""
    alarm = detect_session_timeout("sess-timeout", elapsed_seconds=2000, timeout_seconds=1800)
    assert alarm is not None
    assert alarm.type == "SESSION_TIMEOUT"
    assert alarm.severity == "MEDIUM"
    assert alarm.context["elapsed_seconds"] == 2000


def test_eval_alarm_session_timeout_not_fired_below_timeout():
    """No SESSION_TIMEOUT alarm when elapsed is below timeout."""
    alarm = detect_session_timeout("sess-timeout", elapsed_seconds=100, timeout_seconds=1800)
    assert alarm is None


# ---------------------------------------------------------------------------
# TOOL_CATEGORY_BIAS
# ---------------------------------------------------------------------------

def test_eval_alarm_tool_category_bias_fires_when_category_exceeds_limit():
    """TOOL_CATEGORY_BIAS alarm (LOW) fires when one category dominates spend."""
    alarm = detect_tool_category_bias("sess-bias", category="web", category_token_share=0.75, limit=0.50)
    assert alarm is not None
    assert alarm.type == "TOOL_CATEGORY_BIAS"
    assert alarm.severity == "LOW"
    assert alarm.context["category"] == "web"


def test_eval_alarm_tool_category_bias_not_fired_below_limit():
    """No TOOL_CATEGORY_BIAS alarm when category share is below limit."""
    alarm = detect_tool_category_bias("sess-bias", category="file_io", category_token_share=0.25, limit=0.50)
    assert alarm is None


# ---------------------------------------------------------------------------
# CHECKPOINT_FAIL
# ---------------------------------------------------------------------------

def test_eval_alarm_checkpoint_fail_has_expected_shape():
    """CHECKPOINT_FAIL alarm (MEDIUM) carries checkpoint name and reason."""
    alarm = alarm_for_checkpoint_failure("sess-cp", checkpoint_name="budget_health", reason="over budget")
    assert alarm.type == "CHECKPOINT_FAIL"
    assert alarm.severity == "MEDIUM"
    assert alarm.context["checkpoint_name"] == "budget_health"
    assert alarm.context["reason"] == "over budget"


# ---------------------------------------------------------------------------
# Alarm deduplication (BUDGET_YELLOW fires only once per session)
# ---------------------------------------------------------------------------

def test_eval_alarm_budget_yellow_deduplicates_per_session(tmp_path):
    """BUDGET_YELLOW fires once per session, not on every turn."""
    client = _client(tmp_path)
    with client:
        started = _start_session(client, daily_used_tokens=650_000)
        _proxy_request(client, started["session_api_key"])
        _proxy_request(client, started["session_api_key"])
        _proxy_request(client, started["session_api_key"])

    artifact = db.build_session_artifact(tmp_path / "harness.db", started["session_id"])
    yellow_alarms = [a for a in artifact["alarms"] if a["type"] == "BUDGET_YELLOW"]
    assert len(yellow_alarms) == 1
