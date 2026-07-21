from foreman_ai_hq import db
from tests.portal.helpers import PORTAL_TOKEN, _client, _portal_headers


def test_live_worker_event_endpoint_requires_auth_and_returns_bounded_incremental_events(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    session = db.create_session(
        database_path,
        task_description="DEMO live events 2099",
        model="opencode/gpt-5.1",
        session_key_hash="d" * 64,
        guardrail_overrides={},
        status="running",
    )
    task = db.create_task(database_path, description="DEMO live events 2099", status="Running", session_id=session["id"])
    run = db.create_worker_run(
        database_path,
        task_id=task["id"],
        session_id=session["id"],
        adapter_id="opencode",
        model="opencode/gpt-5.1",
        tracking_mode="native_usage",
        command_plan={"command": ["opencode"], "env": {}, "metadata": {}},
    )
    first = db.record_worker_run_event(
        database_path,
        worker_run_id=run["id"],
        session_id=session["id"],
        task_id=task["id"],
        layer="worker_harness",
        kind="agent_message",
        title="DEMO message",
        detail={"text": "password=DEMO_SECRET_999"},
    )
    second = db.record_worker_run_event(
        database_path,
        worker_run_id=run["id"],
        session_id=session["id"],
        task_id=task["id"],
        layer="worker_harness",
        kind="token",
        title="Provisional usage",
        detail={"total_tokens": 9},
    )

    with _client(tmp_path) as client:
        unauthorized = client.get(f"/api/sessions/{session['id']}/events")
        response = client.get(f"/api/sessions/{session['id']}/events?since_id={first['id']}", headers=_portal_headers())

    assert unauthorized.status_code == 401
    assert response.status_code == 200
    payload = response.json()
    assert payload["next_since_id"] == second["id"]
    assert payload["events"] == [{
        "id": second["id"],
        "created_at": second["created_at"],
        "kind": "token",
        "layer": "worker_harness",
        "title": "Provisional usage",
        "detail_summary": "total_tokens=9",
    }]
    assert "detail" not in payload["events"][0]

    # The since_id filter above excludes the secret-bearing event, so asserting on
    # this payload would prove nothing. Fetch it directly instead.
    with _client(tmp_path) as client:
        full = client.get(f"/api/sessions/{session['id']}/events", headers=_portal_headers()).json()

    streamed = [event for event in full["events"] if event["kind"] == "agent_message"]
    assert streamed, "expected the streamed agent_message event in the unfiltered page"
    assert "DEMO_SECRET_999" not in str(full), (
        "streamed agent text reaches the browser verbatim; secrets must be redacted upstream"
    )


def test_live_worker_event_endpoint_reports_has_more_only_when_more_events_exist(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    session = db.create_session(database_path, task_description="DEMO 2099 events", model="opencode/gpt-5.1", session_key_hash="e" * 64, guardrail_overrides={})
    task = db.create_task(database_path, description="DEMO 2099 events", status="Running", session_id=session["id"])
    run = db.create_worker_run(database_path, task_id=task["id"], session_id=session["id"], adapter_id="opencode", model="opencode/gpt-5.1", tracking_mode="native_usage", command_plan={"command": ["opencode"], "env": {}, "metadata": {}})
    for index in range(100):
        db.record_worker_run_event(database_path, worker_run_id=run["id"], session_id=session["id"], task_id=task["id"], layer="worker_harness", kind="status", title=f"DEMO event {index}", detail={})

    with _client(tmp_path) as client:
        payload = client.get(f"/api/sessions/{session['id']}/events", headers=_portal_headers()).json()

    assert len(payload["events"]) == 100
    assert payload["has_more"] is False

    overflow = db.record_worker_run_event(database_path, worker_run_id=run["id"], session_id=session["id"], task_id=task["id"], layer="worker_harness", kind="status", title="DEMO event 100", detail={})
    with db.connect(database_path) as conn:
        conn.execute("update worker_run_events set created_at = ? where id = ?", ("2099-12-31T00:00:00+00:00", payload["events"][-1]["id"]))
        conn.execute("update worker_run_events set created_at = ? where id = ?", ("2099-11-30T00:00:00+00:00", overflow["id"]))
    with _client(tmp_path) as client:
        first_page = client.get(f"/api/sessions/{session['id']}/events", headers=_portal_headers()).json()
        final_page = client.get(f"/api/sessions/{session['id']}/events?since_id={first_page['next_since_id']}", headers=_portal_headers()).json()

    assert first_page["has_more"] is True
    assert [event["id"] for event in final_page["events"]] == [overflow["id"]]
    assert final_page["has_more"] is False


def test_worker_run_event_detail_summary_renders_unmodelled_shapes_without_dumping_blobs():
    """Control-plane details must read as key=value, and nested blobs must stay out."""
    summary = db._worker_run_event_detail_summary(
        {"adapter_id": "demo_worker", "model": "claude-sonnet-5", "tracking_mode": "native_usage"}
    )
    assert summary == "adapter_id=demo_worker; model=claude-sonnet-5; tracking_mode=native_usage"

    # A command plan is a nested blob: summarized away, never inlined into a feed row.
    assert db._worker_run_event_detail_summary({"command_plan": {"command": ["foremanctl"], "env": {}}}) == ""
    assert "{" not in db._worker_run_event_detail_summary({"documents": ["README.md"], "manifests": []})


def test_worker_run_event_detail_summary_extracts_streamed_content():
    assert db._worker_run_event_detail_summary({"text": "Hello world"}) == "Hello world"
    assert db._worker_run_event_detail_summary({"arguments": '{"path": "src/main.py"}'}) == 'arguments={"path": "src/main.py"}'
    assert db._worker_run_event_detail_summary({"input_tokens": 12, "output_tokens": 3}) == "input_tokens=12; output_tokens=3"
    assert db._worker_run_event_detail_summary({"status": "started"}) == "status=started"
    assert db._worker_run_event_detail_summary({}) == ""
