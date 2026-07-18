import re

from foreman_ai_hq import db
from tests.portal.helpers import PORTAL_TOKEN, _client, _portal_headers, _project_metadata


def _seed_report(tmp_path):
    path = tmp_path / "harness.db"
    db.init_db(path)
    session = db.create_session(
        path,
        task_description="DEMO 2099 session " + "task evidence " * 1800 + "END2099TASK",
        model="opencode/gpt-5.5",
        session_key_hash="s" * 64,
        guardrail_overrides={},
        status="running",
    )
    db.record_token_turn(
        path,
        session_id=session["id"],
        model="opencode/gpt-5.5",
        prompt_tokens=300,
        completion_tokens=200,
        cost=0.02,
        raw_usage={
            "total_tokens": 500,
            "input_tokens": 300,
            "spend_category": "worker_execution",
            "payload": "api_key=DEMO_SECRET_999 " + "raw evidence " * 1800 + "END2099RAW",
            "credential": "opaque-demo-credential-999",
            "Cookie": "opaque-demo-cookie-999",
            "X-Auth": "opaque-demo-auth-999",
            "GITHUB_PAT": "opaque-demo-pat-999",
        },
    )
    db.record_guardrail_snapshot(path, session_id=session["id"], zone="yellow", decision={"max_tokens": 2048})
    db.record_alarm(
        path,
        session_id=session["id"],
        alarm={"id": "alarm-demo-999", "type": "BUDGET_YELLOW", "severity": "MEDIUM", "recommended_action": "Review DEMO spend."},
    )
    db.record_checkpoint_result(
        path,
        session_id=session["id"],
        checkpoint={"name": "budget_health", "passed": False, "details": {"reason": "DEMO " + "detail " * 4000}},
    )
    task = db.create_task(
        path,
        description="DEMO 2099 session",
        status="Review",
        session_id=session["id"],
        metadata={
            **_project_metadata(path, tmp_path / "DEMO-project-999"),
            "agent_review": {
                "status": "completed",
                "recommendation": "approve",
                "summary": "DEMO review summary",
                "findings": [{"severity": "low", "message": "DEMO finding 999"}],
                "model": "claude-demo-999",
                "reviewed_at": "2099-01-02T03:04:05+00:00",
            },
        },
    )
    run = db.create_worker_run(
        path,
        task_id=task["id"],
        session_id=session["id"],
        adapter_id="opencode",
        model="opencode/gpt-5.5",
        tracking_mode="native_usage",
        command_plan={"command": ["opencode", "run", "DEMO"], "env": {"password": "DEMO_SECRET_999"}},
        metadata={
            "connected_project_name": "DEMO-project-999",
            "repo_context_brief": {
                "documents": [{"path": "AGENTS.md", "excerpt": "DEMO instructions"}],
                "manifests": ["pyproject.toml"],
                "text": "DEMO repo context " + "context " * 6000 + "END2099REPO",
            },
        },
    )
    db.record_worker_run_event(
        path,
        worker_run_id=run["id"],
        session_id=session["id"],
        task_id=task["id"],
        kind="launch",
        title="DEMO Worker launched",
        detail={"Bearer DEMO_SECRET_999": "hidden", "status": "running", "detail": "x" * 21000},
    )
    return session["id"]


def test_sessions_api_is_authenticated_exact_bounded_and_active(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    session_id = _seed_report(tmp_path)
    with _client(tmp_path) as client:
        assert client.get("/api/sessions").status_code == 401
        response = client.get("/api/sessions?offset=0&limit=1", headers=_portal_headers())
        invalid = [client.get(url, headers=_portal_headers()).status_code for url in (
            "/api/sessions?offset=-1", "/api/sessions?limit=0", "/api/sessions?limit=101", "/api/sessions?limit=nope",
        )]
    assert invalid == [422, 422, 422, 422]
    body = response.json()
    assert set(body) == {"sessions", "pagination", "has_active", "poll_after_ms"}
    assert body["has_active"] is True and body["poll_after_ms"] == 5000
    row = body["sessions"][0]
    assert set(row) == {"id", "kind", "task_preview", "model", "status", "active", "token_totals", "evidence_counts", "current_zone", "alarm_count", "report_href"}
    assert row["id"] == session_id and row["report_href"] == f"/sessions/{session_id}"
    assert len(row["task_preview"]) == 240
    assert "session_key_hash" not in response.text and "guardrail_overrides" not in response.text


def test_report_api_exact_parity_redaction_and_continuations(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    session_id = _seed_report(tmp_path)
    with _client(tmp_path) as client:
        assert client.get(f"/api/sessions/{session_id}/report").status_code == 401
        response = client.get(f"/api/sessions/{session_id}/report", headers=_portal_headers())
        report = response.json()
        task_href = report["session"]["task"]["full_href"]
        raw_href = report["tokens"]["log"]["items"][0]["raw_usage"]["full_href"]
        repo_href = report["repo_context_briefs"]["items"][0]["text"]["full_href"]
        full = [client.get(href, headers=_portal_headers()) for href in (task_href, raw_href, repo_href)]
    assert response.status_code == 200
    assert set(report) == {"session", "summary", "tokens", "zone_timeline", "worker_timeline", "repo_context_briefs", "alarms", "checkpoints", "related_agent_review", "freshness", "links"}
    assert set(report["summary"]["evidence_counts"]) == {"alarms", "checkpoints", "failed_checkpoints", "worker_runs", "worker_events", "error_events"}
    assert report["tokens"]["provider_totals"]["total_tokens"] == 500
    assert report["tokens"]["normalized"]["by_category"]["worker_execution"] == 500
    assert set(report["tokens"]["normalized"]) == {"total_tokens", "by_category"}
    assert report["related_agent_review"]["review_total_tokens"] is None
    assert all(item.status_code == 200 and item.headers["cache-control"] == "no-store" for item in full)
    assert "END2099TASK" in full[0].text and "END2099RAW" in full[1].text and "END2099REPO" in full[2].text
    assert '"input_tokens": 300' in full[1].text
    assert "DEMO_SECRET_999" not in full[1].text
    assert all(secret not in full[1].text for secret in ("opaque-demo-credential-999", "opaque-demo-cookie-999", "opaque-demo-auth-999", "opaque-demo-pat-999"))
    assert "session_key_hash" not in response.text and "guardrail_overrides" not in response.text


def test_evidence_pages_are_allowlisted_bounded_and_stable(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    session_id = _seed_report(tmp_path)
    with _client(tmp_path) as client:
        for collection in ("token-log", "zone-timeline", "worker-timeline", "repo-context", "alarms", "checkpoints", "agent-review-findings", "repo-documents-0", "repo-manifests-0"):
            response = client.get(f"/api/sessions/{session_id}/evidence/{collection}?limit=1", headers=_portal_headers())
            assert response.status_code == 200, collection
            assert set(response.json()) == {"items", "pagination"}
            assert set(response.json()["pagination"]) == {"offset", "limit", "total", "has_more", "next_href"}
        assert client.get(f"/api/sessions/{session_id}/evidence/../../secrets", headers=_portal_headers()).status_code == 404
        assert client.get(f"/api/sessions/{session_id}/evidence/worker-timeline?limit=201", headers=_portal_headers()).status_code == 422
        assert client.get(f"/api/sessions/{session_id}/evidence/repo-documents-00", headers=_portal_headers()).status_code == 404


def test_freshness_is_opaque_stable_and_changes_on_append_and_status(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    session_id = _seed_report(tmp_path)
    path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        first = client.get(f"/api/sessions/{session_id}/freshness", headers=_portal_headers()).json()
        stable = client.get(f"/api/sessions/{session_id}/freshness", headers=_portal_headers()).json()
        db.record_token_turn(path, session_id=session_id, model="demo", prompt_tokens=1, completion_tokens=1, cost=0, raw_usage={"total_tokens": 2})
        appended = client.get(f"/api/sessions/{session_id}/freshness", headers=_portal_headers()).json()
        db.update_session_status(path, session_id, "completed")
        terminal = client.get(f"/api/sessions/{session_id}/freshness", headers=_portal_headers()).json()
        report = client.get(f"/api/sessions/{session_id}/report", headers=_portal_headers()).json()
    assert first == stable
    assert set(first) == {"session_id", "status", "active", "version", "last_evidence_at"}
    assert re.fullmatch(r"[0-9a-f]{64}", first["version"])
    assert appended["version"] != first["version"]
    assert terminal["version"] != appended["version"] and terminal["active"] is False
    assert report["freshness"] == terminal


def test_agent_review_session_resolves_failed_review_outcome(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    path = tmp_path / "harness.db"
    db.init_db(path)
    worker = db.create_session(path, task_description="DEMO worker 2099", model="worker-demo", session_key_hash="w" * 64, guardrail_overrides={}, status="completed")
    review = db.create_session(path, task_description="DEMO Agent Review 2099", model="review-demo", session_key_hash="r" * 64, guardrail_overrides={}, status="failed")
    task = db.create_task(path, description="DEMO reviewed task 2099", status="Review", session_id=worker["id"], metadata={})
    db.update_task_metadata(path, task["id"], lambda metadata: {
        **metadata,
        "agent_review": {
            "review_session_id": review["id"],
            "status": "failed",
            "recommendation": "manual review",
            "summary": "DEMO review could not complete 2099",
            "error": "DEMO provider outage 2099",
            "findings": [{"severity": "high", "message": "DEMO finding 2099"}],
            "model": "review-demo",
        },
    })
    with _client(tmp_path) as client:
        report = client.get(f"/api/sessions/{review['id']}/report", headers=_portal_headers()).json()
        sessions = client.get("/api/sessions", headers=_portal_headers()).json()["sessions"]
    assert report["session"]["kind"] == "Agent Review"
    assert report["summary"]["selected_project"]["preview"] == "Agent Review: DEMO reviewed task 2099"
    assert report["summary"]["result"]["preview"] == "DEMO provider outage 2099"
    assert report["summary"]["requires_review"] is True
    assert report["related_agent_review"]["recommendation"] == "manual review"
    assert report["related_agent_review"]["error"]["preview"] == "DEMO provider outage 2099"
    assert report["related_agent_review"]["review_session_href"] is None
    assert next(row for row in sessions if row["id"] == review["id"])["kind"] == "Agent Review"


def test_missing_and_unknown_session_handoffs_return_404(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        for url in (
            "/api/sessions/missing/report",
            "/api/sessions/missing/freshness",
            "/api/sessions/missing/evidence/token-log",
            "/api/sessions/missing/text/task",
        ):
            response = client.get(url, headers=_portal_headers())
            assert response.status_code == 404
            assert "session not found" in response.text
