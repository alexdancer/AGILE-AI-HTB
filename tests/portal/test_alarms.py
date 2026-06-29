from agile_ai_htb import db
from tests.portal.helpers import PORTAL_TOKEN, _client, _portal_headers

def test_alarms_browser_accept_renders_html_inbox_without_breaking_json_api(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": "Alarm inbox", "model": "claude-haiku"},
        ).json()
        db.record_alarm(
            tmp_path / "harness.db",
            session_id=started["session_id"],
            alarm={
                "id": "alarm-inbox-1",
                "type": "DAILY_CAP_EXCEEDED",
                "severity": "HIGH",
                "context": {"daily_cap": 100},
                "recommended_action": "Ask human to raise budget.",
            },
        )

        resolved = client.post("/alarms/alarm-inbox-1/resolve", json={"action": "continue"})
        assert resolved.status_code == 200

        api_response = client.get("/alarms")
        html_response = client.get(
            "/alarms",
            headers={**_portal_headers(), "accept": "text/html"},
        )

    assert api_response.status_code == 200
    assert api_response.json()["alarms"][0]["id"] == "alarm-inbox-1"
    assert html_response.status_code == 200
    assert "text/html" in html_response.headers["content-type"]
    assert "Resolved" in html_response.text
    assert "DAILY_CAP_EXCEEDED" in html_response.text
    assert started["session_id"] in html_response.text
    assert "Ask human to raise budget." in html_response.text

