from foreman_ai_hq import db
from foreman_ai_hq.project_context import project_task_metadata
from tests.portal.helpers import PORTAL_TOKEN, _client, _connect_project, _portal_headers


def test_portal_renders_worker_token_component_breakdown(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    project = _connect_project(database_path, tmp_path / "project")
    session = db.create_session(
        database_path,
        task_description="DEMO Worker token component slice",
        model="opencode/gpt-5.1",
        session_key_hash="component-hash",
        guardrail_overrides={},
        status="completed",
    )
    task = db.create_task(
        database_path,
        description="DEMO Worker token component slice",
        status="Review",
        estimate_tokens=200,
        recommended_model="opencode/gpt-5.1",
        actual_tokens=90,
        session_id=session["id"],
        metadata=project_task_metadata(project),
    )
    run = db.create_worker_run(
        database_path,
        task_id=task["id"],
        session_id=session["id"],
        adapter_id="opencode",
        model="opencode/gpt-5.1",
        tracking_mode="native_usage",
        command_plan={"command": ["opencode", "run"]},
    )
    db.mark_worker_run_completed(database_path, run["id"], returncode=0)
    db.record_token_turn(
        database_path,
        session_id=session["id"],
        usage_kind="task_execution",
        model="opencode/gpt-5.1",
        prompt_tokens=70,
        completion_tokens=50,
        cost=0.25,
        raw_usage={
            "usage": {
                "input_tokens": 40,
                "cache_read_input_tokens": 30,
                "output_tokens": 45,
                "reasoning_tokens": 5,
                "total_tokens": 120,
            },
            "run_binding": {"session_id": session["id"]},
        },
    )
    db.record_token_turn(
        database_path,
        session_id=session["id"],
        usage_kind="task_breakdown",
        model="control-plane/gpt-5.4-mini",
        prompt_tokens=9000,
        completion_tokens=999,
        cost=1.0,
        raw_usage={"input_tokens": 9000, "output_tokens": 999, "total_tokens": 9999},
    )

    with _client(tmp_path) as client:
        dashboard = client.get("/api/dashboard", headers=_portal_headers())
        report = client.get(f"/api/sessions/{session['id']}/report", headers=_portal_headers())
        board = client.get(f"/api/projects/{project['id']}/board", headers=_portal_headers())

    assert dashboard.status_code == 200
    dashboard_payload = dashboard.json()
    worker = dashboard_payload["worker_execution"]
    assert worker["status_split"]["completed"] == 90
    assert worker["components"]["cost"] == 0.25
    component_labels = {item["label"] for item in worker["components"]["items"]}
    assert "normalized actual/task budget" in component_labels
    assert "provider raw total/evidence" in component_labels
    assert "fresh input/new prompt text" in component_labels
    assert "cache read/reused context" in component_labels

    assert report.status_code == 200
    report_payload = report.json()
    assert report_payload["tokens"]["worker_components"]["available"] is True
    report_labels = {item["label"] for item in report_payload["tokens"]["worker_components"]["items"]}
    assert "normalized actual/task budget" in report_labels
    assert "provider raw total/evidence" in report_labels
    assert "reasoning" in report_labels

    assert board.status_code == 200
    board_payload = board.json()
    review_tasks = board_payload["tasks_by_status"]["Review"]
    assert any(t["id"] == task["id"] and t["actual_tokens"] == 90 for t in review_tasks)


def test_dashboard_empty_worker_components_show_unavailable_state(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    with _client(tmp_path) as client:
        response = client.get("/api/dashboard", headers=_portal_headers())

    assert response.status_code == 200
    assert response.json()["worker_execution"]["components"]["available"] is False
