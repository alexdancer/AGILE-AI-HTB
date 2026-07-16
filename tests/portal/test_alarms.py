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

        # "/alarms" with Accept: text/html is the retired Jinja HTML arm (now the
        # missing-build recovery response); its React replacement is this
        # authenticated JSON handoff. The JSON-polling arm of "/alarms" itself
        # (no Accept: text/html) is unaffected by retirement and already proven
        # by test_react_shell.test_alarms_json_polling_is_unaffected_by_retirement,
        # so it is only re-used below via ``api_response`` as before.
        before = client.get("/api/alarms", headers=_portal_headers())
        dismissed = client.post(
            "/alarms/alarm-inbox-1/resolve",
            headers={**_portal_headers(), "accept": "text/html"},
            data={"action": "continue"},
            follow_redirects=False,
        )
        after = client.get("/api/alarms", headers=_portal_headers())
        api_response = client.get("/alarms", params={"resolved": True})

    assert api_response.status_code == 200
    assert api_response.json()["alarms"][0]["id"] == "alarm-inbox-1"
    assert api_response.json()["alarms"][0]["resolved_at"]

    assert before.status_code == 200
    before_alarm = before.json()["alarms"][0]
    assert before_alarm["id"] == "alarm-inbox-1"
    assert before_alarm["type"] == "DAILY_CAP_EXCEEDED"
    assert before_alarm["session_id"] == started["session_id"]
    assert before_alarm["recommended_action"] == "Ask human to raise budget."
    # The "Dismiss" button in the retired markup was driven by this same
    # available-actions list; the browser-observable "action=".../resolve""
    # form attribute is exercised for real by the actual POST below.
    assert any(a.get("action") == "continue" for a in before_alarm["available_actions"])

    assert dismissed.status_code == 303
    assert dismissed.headers["location"] == "/alarms"

    assert after.status_code == 200
    # Once resolved it drops out of the default "open" filter, the backend
    # equivalent of the retired page no longer listing it in the open inbox.
    assert after.json()["alarms"] == []

