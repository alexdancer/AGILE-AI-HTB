from pathlib import Path

from fastapi.testclient import TestClient

from agile_ai_htb.app import create_app
from agile_ai_htb.db import get_session, record_alarm
from agile_ai_htb.settings import Settings


ROOT = Path(__file__).resolve().parents[2]


def _client(tmp_path):
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    return TestClient(create_app(settings))


def _start_session(client):
    return client.post(
        "/session/start",
        json={"task_description": "Review alarm", "model": "claude-haiku"},
    ).json()["session_id"]


def test_list_alarms_filters_by_session_type_severity_and_resolved_state(tmp_path):
    with _client(tmp_path) as client:
        session_id = _start_session(client)
        other_session_id = _start_session(client)
        db_path = tmp_path / "harness.db"
        record_alarm(
            db_path,
            session_id=session_id,
            alarm={
                "id": "alarm-api-1",
                "type": "DAILY_CAP_EXCEEDED",
                "severity": "HIGH",
                "context": {"daily_used_tokens": 100},
                "recommended_action": "Ask human.",
            },
        )
        record_alarm(
            db_path,
            session_id=other_session_id,
            alarm={
                "id": "alarm-api-2",
                "type": "BUDGET_YELLOW",
                "severity": "LOW",
                "context": {},
                "recommended_action": "Warn.",
            },
        )

        all_response = client.get("/alarms")
        filtered = client.get(
            "/alarms",
            params={"session_id": session_id, "type": "DAILY_CAP_EXCEEDED", "severity": "HIGH", "resolved": False},
        )

    assert all_response.status_code == 200
    assert {alarm["id"] for alarm in all_response.json()["alarms"]} == {"alarm-api-1", "alarm-api-2"}
    assert filtered.status_code == 200
    assert [alarm["id"] for alarm in filtered.json()["alarms"]] == ["alarm-api-1"]
    assert filtered.json()["alarms"][0]["resolved_at"] is None


def test_resolve_alarm_records_action_history_and_keeps_alarm_visible(tmp_path):
    with _client(tmp_path) as client:
        session_id = _start_session(client)
        record_alarm(
            tmp_path / "harness.db",
            session_id=session_id,
            alarm={
                "id": "alarm-resolve-1",
                "type": "SESSION_CAP_EXCEEDED",
                "severity": "MEDIUM",
                "context": {},
                "recommended_action": "Review session.",
            },
        )

        resolved = client.post(
            "/alarms/alarm-resolve-1/resolve",
            json={"action": "raise_budget", "payload": {"session_cap_tokens": 300_000}},
        )
        listed = client.get("/alarms", params={"resolved": True})

    assert resolved.status_code == 200
    assert resolved.json()["alarm"]["id"] == "alarm-resolve-1"
    assert resolved.json()["alarm"]["resolved_at"]
    assert resolved.json()["action"]["action"] == "raise_budget"
    assert resolved.json()["action"]["payload"] == {"session_cap_tokens": 300_000}
    assert [alarm["id"] for alarm in listed.json()["alarms"]] == ["alarm-resolve-1"]
    session = get_session(tmp_path / "harness.db", session_id)
    assert session["guardrail_overrides"]["budget"]["session_cap_tokens"] == 300_000


def test_abort_session_alarm_action_updates_session_status(tmp_path):
    with _client(tmp_path) as client:
        session_id = _start_session(client)
        record_alarm(
            tmp_path / "harness.db",
            session_id=session_id,
            alarm={
                "id": "alarm-abort-1",
                "type": "LOOP_DETECTED",
                "severity": "MEDIUM",
                "context": {},
                "recommended_action": "Review session.",
            },
        )

        response = client.post("/alarms/alarm-abort-1/resolve", json={"action": "abort_session"})

    assert response.status_code == 200
    assert get_session(tmp_path / "harness.db", session_id)["status"] == "aborted"


def test_adjust_guardrail_alarm_action_updates_session_overrides(tmp_path):
    with _client(tmp_path) as client:
        session_id = _start_session(client)
        record_alarm(
            tmp_path / "harness.db",
            session_id=session_id,
            alarm={
                "id": "alarm-adjust-1",
                "type": "TOOL_CATEGORY_BIAS",
                "severity": "LOW",
                "context": {},
                "recommended_action": "Adjust guardrail.",
            },
        )

        response = client.post(
            "/alarms/alarm-adjust-1/resolve",
            json={"action": "adjust_guardrail", "payload": {"tool_category_limit": {"limit": 0.75}}},
        )

    assert response.status_code == 200
    assert get_session(tmp_path / "harness.db", session_id)["guardrail_overrides"]["tool_category_limit"] == {"limit": 0.75}


def test_resolve_alarm_rejects_unknown_action_and_missing_alarm(tmp_path):
    with _client(tmp_path) as client:
        bad_action = client.post("/alarms/missing/resolve", json={"action": "delete"})
        missing = client.post("/alarms/missing/resolve", json={"action": "continue"})

    assert bad_action.status_code == 422
    assert missing.status_code == 404
