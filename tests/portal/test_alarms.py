from foreman_ai_hq import db
from tests.portal.helpers import PORTAL_TOKEN, _client, _portal_headers

def test_alarms_browser_accept_dismisses_open_alarm_without_breaking_json_api(tmp_path, monkeypatch):
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

        html_before = client.get(
            "/alarms",
            headers={**_portal_headers(), "accept": "text/html"},
        )
        dismissed = client.post(
            "/alarms/alarm-inbox-1/resolve",
            headers={**_portal_headers(), "accept": "text/html"},
            data={"action": "continue"},
            follow_redirects=False,
        )
        html_after = client.get(
            dismissed.headers["location"],
            headers={**_portal_headers(), "accept": "text/html"},
        )
        api_response = client.get("/alarms", params={"resolved": True})

    assert api_response.status_code == 200
    assert api_response.json()["alarms"][0]["id"] == "alarm-inbox-1"
    assert api_response.json()["alarms"][0]["resolved_at"]
    assert html_before.status_code == 200
    assert "text/html" in html_before.headers["content-type"]
    assert "Dismiss" in html_before.text
    assert 'action="/alarms/alarm-inbox-1/resolve"' in html_before.text
    assert "DAILY_CAP_EXCEEDED" in html_before.text
    assert started["session_id"] in html_before.text
    assert "Ask human to raise budget." in html_before.text
    assert dismissed.status_code == 303
    assert dismissed.headers["location"] == "/alarms"
    assert html_after.status_code == 200
    assert "Recently resolved" not in html_after.text
    assert "DAILY_CAP_EXCEEDED" not in html_after.text
    assert "Ask human to raise budget." not in html_after.text

