import json

import pytest

from agile_ai_htb import db
from agile_ai_htb.routes import react_shell
from tests.portal.helpers import PORTAL_TOKEN, _client, _portal_headers, _project_metadata


@pytest.fixture(autouse=True)
def _jinja_fallback(tmp_path, monkeypatch):
    build_dir = tmp_path / "missing-react-build"
    build_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)


def test_sessions_index_renders_mockup_style_session_table(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": "Review live portal", "model": "claude-haiku"},
        ).json()
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=started["session_id"],
            model="claude-haiku",
            prompt_tokens=80,
            completion_tokens=20,
            cost=0.01,
            raw_usage={"total_tokens": 100},
        )
        response = client.get("/sessions", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "All sessions" in html
    assert "summary before raw report" in html
    assert "table-wrap" in html
    assert "Review live portal" in html
    assert "100" in html
    assert "0 runs" in html
    assert "0 events" in html
    assert "zone:" in html


def test_sessions_index_compacts_long_task_text_preserves_scan_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    long_task = "Review compact sessions " + ("visible summary " * 20) + "FULL_TASK_TAIL_2099"
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": long_task, "model": "claude-haiku"},
        ).json()
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=started["session_id"],
            model="claude-haiku",
            prompt_tokens=1234,
            completion_tokens=56,
            cost=0.01,
            raw_usage={"total_tokens": 1290},
        )

        index = client.get("/sessions", headers=_portal_headers())
        report = client.get(f"/sessions/{started['session_id']}", headers=_portal_headers())

    assert index.status_code == 200
    html = index.text
    assert "compact-text lines-2" in html
    assert "Review compact sessions" in html
    assert "FULL_TASK_TAIL_2099" not in html
    assert f"/sessions/{started['session_id']}" in html
    assert "claude-haiku" in html
    assert "1,234" in html
    assert "56" in html
    assert "1,290" in html
    assert "0 runs" in html
    assert "0 events" in html
    assert "zone:" in html
    assert report.status_code == 200
    assert "FULL_TASK_TAIL_2099" in report.text


def test_sessions_index_and_report_label_agent_review_accounting(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    db.init_db(tmp_path / "harness.db")
    review_session = db.create_session(
        tmp_path / "harness.db",
        task_description="Agent review for task DEMO_TASK_999",
        model="anthropic/claude-sonnet-4-20250514",
        session_key_hash="a" * 64,
        guardrail_overrides={"spend_category": "agent_review", "task_id": "DEMO_TASK_999"},
        status="completed",
    )
    db.record_token_turn(
        tmp_path / "harness.db",
        session_id=review_session["id"],
        usage_kind="reporting",
        model="anthropic/claude-sonnet-4-20250514",
        prompt_tokens=70,
        completion_tokens=30,
        cost=0.01,
        raw_usage={
            "total_tokens": 100,
            "spend_category": "agent_review",
            "response": {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "DEMO review summary 2099.",
                                    "recommendation": "approve",
                                    "findings": [],
                                }
                            )
                        }
                    }
                ]
            },
        },
    )

    with _client(tmp_path) as client:
        index = client.get("/sessions", headers=_portal_headers())
        report = client.get(f"/sessions/{review_session['id']}", headers=_portal_headers())

    assert index.status_code == 200
    assert "Agent Review" in index.text
    assert "100" in index.text
    assert "0 runs" in index.text
    assert report.status_code == 200
    assert "Agent Review" in report.text
    assert "Review source" in report.text
    assert "Control Plane" in report.text
    assert "reporting_summary" in report.text
    assert "approve · DEMO review summary 2099." in report.text
    assert "Agent Review for task DEMO_TASK_999" in report.text
    assert "missing Worker Run evidence" not in report.text
    breakdown = db.session_token_breakdown(tmp_path / "harness.db", review_session["id"])
    assert breakdown["by_category"]["reporting_summary"] == 100
    assert breakdown["by_source"]["control_plane"] == 100


def test_worker_session_report_shows_related_agent_review_results_and_tokens(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    worker_session = db.create_session(
        database_path,
        task_description="DEMO reviewed worker session 2099",
        model="opencode/gpt-5.5",
        session_key_hash="w" * 64,
        guardrail_overrides={},
        status="completed",
    )
    review_session = db.create_session(
        database_path,
        task_description="Agent review for DEMO_TASK_999",
        model="anthropic/claude-sonnet-4-20250514",
        session_key_hash="r" * 64,
        guardrail_overrides={"spend_category": "agent_review", "task_id": "DEMO_TASK_999"},
        status="completed",
    )
    db.record_token_turn(
        database_path,
        session_id=worker_session["id"],
        model="opencode/gpt-5.5",
        prompt_tokens=300,
        completion_tokens=200,
        cost=0.02,
        raw_usage={"total_tokens": 500, "spend_category": "worker_execution", "usage_source": "harness_proxy"},
    )
    db.record_token_turn(
        database_path,
        session_id=review_session["id"],
        usage_kind="reporting",
        model="anthropic/claude-sonnet-4-20250514",
        prompt_tokens=40,
        completion_tokens=9,
        cost=0.01,
        raw_usage={"total_tokens": 49, "spend_category": "reporting_summary", "usage_source": "control_plane", "reporting_kind": "agent_review"},
    )
    task = db.create_task(
        database_path,
        description="DEMO reviewed worker session 2099",
        status="Review",
        actual_tokens=500,
        session_id=worker_session["id"],
        metadata={
            "agent_review": {
                "status": "completed",
                "summary": "DEMO Agent Review summary 2099",
                "recommendation": "approve",
                "findings": [{"severity": "low", "message": "DEMO finding 2099"}],
                "reviewed_at": "2099-01-02T03:04:05+00:00",
                "review_session_id": review_session["id"],
                "model": "anthropic/claude-sonnet-4-20250514",
                "token_totals": {"prompt_tokens": 40, "completion_tokens": 9, "total_tokens": 49},
            }
        },
    )

    with _client(tmp_path) as client:
        response = client.get(f"/sessions/{worker_session['id']}", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Agent Review results" in html
    assert "completed · approve" in html
    assert "DEMO Agent Review summary 2099" in html
    assert "DEMO finding 2099" in html
    assert "reviewed: 2099-01-02T03:04:05+00:00" in html
    assert "anthropic/claude-sonnet-4-20250514" in html
    assert "49 review/control-plane tokens" in html
    assert f'/sessions/{review_session["id"]}' in html
    assert "500" in html
    worker_breakdown = db.session_token_breakdown(database_path, worker_session["id"])
    assert worker_breakdown["by_category"]["worker_execution"] == 500
    assert worker_breakdown["by_category"]["reporting_summary"] == 0
    assert db.get_task(database_path, task["id"])["actual_tokens"] == 500


def test_worker_session_report_shows_failed_agent_review_without_fabricated_zero_tokens(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    worker_session = db.create_session(
        database_path,
        task_description="DEMO failed review worker session 2099",
        model="opencode/gpt-5.5",
        session_key_hash="w" * 64,
        guardrail_overrides={},
        status="completed",
    )
    review_session = db.create_session(
        database_path,
        task_description="Failed Agent review for DEMO_TASK_999",
        model="anthropic/claude-sonnet-4-20250514",
        session_key_hash="r" * 64,
        guardrail_overrides={"spend_category": "agent_review", "task_id": "DEMO_TASK_999"},
        status="failed",
    )
    db.create_task(
        database_path,
        description="DEMO failed review worker session 2099",
        status="Review",
        actual_tokens=500,
        session_id=worker_session["id"],
        metadata={
            "agent_review": {
                "status": "failed",
                "summary": "Agent Review failed; operator can still mark done or block manually.",
                "recommendation": "needs_changes",
                "findings": [],
                "reviewed_at": "2099-01-02T03:04:05+00:00",
                "review_session_id": review_session["id"],
                "model": "anthropic/claude-sonnet-4-20250514",
                "token_totals": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "error": "DEMO provider timeout 2099",
            }
        },
    )

    with _client(tmp_path) as client:
        response = client.get(f"/sessions/{worker_session['id']}", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Agent Review results" in html
    assert "failed · needs_changes" in html
    assert "Agent Review failed; operator can still mark done or block manually." in html
    assert "DEMO provider timeout 2099" in html
    assert "reviewed: 2099-01-02T03:04:05+00:00" in html
    assert "review tokens unavailable" in html
    assert "0 review/control-plane tokens" not in html


def test_session_report_renders_totals_alarm_checkpoint_without_internal_artifact_link(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": "Audit session", "model": "claude-haiku"},
        ).json()
        session_id = started["session_id"]
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=session_id,
            model="claude-haiku",
            prompt_tokens=300,
            completion_tokens=200,
            cost=0.02,
            raw_usage={"total_tokens": 500},
        )
        db.record_guardrail_snapshot(
            tmp_path / "harness.db",
            session_id=session_id,
            zone="yellow",
            decision={"blocked_tools": ["web_search"], "max_tokens": 2048},
        )
        db.record_alarm(
            tmp_path / "harness.db",
            session_id=session_id,
            alarm={
                "id": "alarm-report-1",
                "type": "CHECKPOINT_FAIL",
                "severity": "MEDIUM",
                "context": {"checkpoint_name": "budget_health"},
                "recommended_action": "Human review required.",
            },
        )
        db.record_checkpoint_result(
            tmp_path / "harness.db",
            session_id=session_id,
            checkpoint={"name": "budget_health", "passed": False, "details": {"reason": "over budget"}},
        )
        task = db.create_task(
            tmp_path / "harness.db",
            description="Audit session",
            status="Running",
            session_id=session_id,
        )
        worker_run = db.create_worker_run(
            tmp_path / "harness.db",
            task_id=task["id"],
            session_id=session_id,
            adapter_id="opencode",
            model="claude-haiku",
            tracking_mode="proxy_governed",
            command_plan={"command": ["opencode"], "env": {}, "metadata": {}},
            metadata={
                "repo_context_brief": {
                    "documents": [{"path": "AGENTS.md", "excerpt": "Use pytest."}],
                    "manifests": ["pyproject.toml"],
                    "text": "Project root: /tmp/demo\n\nRepo instructions/docs:\n- AGENTS.md:\nUse pytest.",
                }
            },
        )
        db.record_worker_run_event(
            tmp_path / "harness.db",
            worker_run_id=worker_run["id"],
            session_id=session_id,
            task_id=task["id"],
            kind="guardrail",
            title="Worker Run failed",
            level="error",
            detail={
                "api_key": "***",
                "documents": ["AGENTS.md"],
                "error_type": "workdir_mismatch",
                "returncode": 124,
                "retryable": True,
            },
        )

        response = client.get(f"/sessions/{session_id}", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Audit session" in html
    assert "500" in html
    assert "yellow" in html
    assert "CHECKPOINT_FAIL" in html
    assert "budget_health" in html
    assert "Requires review" in html
    assert "Status / result" in html
    assert "review needed" in html
    assert "Worker launch" in html
    assert "opencode" in html
    assert "proxy_governed" in html
    assert "target: opencode" in html
    assert "Usage / guardrails" in html
    assert "Evidence coverage" in html
    assert "1 runs" in html
    assert "1 timeline events" in html
    assert "1 errors" in html
    assert "missing project evidence" in html
    assert "raw timeline evidence" in html
    assert "raw prompt context evidence" in html
    assert f"/session/{session_id}/artifact" not in html
    assert "session_key_hash" not in html
    assert "guardrail_overrides" not in html
    assert "Worker Run timeline" in html
    assert "Worker Run failed" in html
    assert "error_type=workdir_mismatch" in html
    assert "returncode=124" in html
    assert "retryable=True" in html
    assert "control_plane" in html
    assert "Repo Context Brief" in html
    assert "AGENTS.md" in html
    assert "pyproject.toml" in html
    assert "Agent Review results" not in html
    assert "review/control-plane tokens" not in html
    assert "***" not in html


def test_session_report_compacts_summary_but_preserves_full_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    long_task = "Compact report task " + ("summary text " * 24) + "REPORT_TASK_TAIL_2099"
    long_command_tail = "LAUNCH_TARGET_TAIL_2099"
    long_detail_tail = "TIMELINE_DETAIL_TAIL_2099"
    long_result_tail = "ERROR_RESULT_TAIL_2099"
    repo_tail = "REPO_CONTEXT_TAIL_2099"

    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": long_task, "model": "claude-haiku"},
        ).json()
        session_id = started["session_id"]
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=session_id,
            model="claude-haiku",
            prompt_tokens=50,
            completion_tokens=10,
            cost=0.01,
            raw_usage={"total_tokens": 60},
        )
        task = db.create_task(
            tmp_path / "harness.db",
            description=long_task,
            status="Running",
            session_id=session_id,
            metadata=_project_metadata(tmp_path / "harness.db", tmp_path / "compact-report-project"),
        )
        worker_run = db.create_worker_run(
            tmp_path / "harness.db",
            task_id=task["id"],
            session_id=session_id,
            adapter_id="opencode",
            model="claude-haiku",
            tracking_mode="native_usage",
            command_plan={
                "command": ["opencode", "run", "--dir", str(tmp_path / "compact-report-project"), "x" * 240, long_command_tail],
                "env": {},
                "metadata": {},
            },
            metadata={
                "connected_project_name": "compact-report-project",
                "repo_context_brief": {
                    "documents": [{"path": "AGENTS.md", "excerpt": "Use pytest."}],
                    "manifests": ["pyproject.toml"],
                    "text": "Repo context\n" + ("bounded raw text\n" * 30) + repo_tail,
                },
            },
        )
        db.mark_worker_run_failed(
            tmp_path / "harness.db",
            worker_run["id"],
            error_type="demo_failure",
            error_message=long_result_tail + (" actionable failure detail" * 40),
            returncode=2,
        )
        db.record_worker_run_event(
            tmp_path / "harness.db",
            worker_run_id=worker_run["id"],
            session_id=session_id,
            task_id=task["id"],
            kind="adapter_complete",
            title="Worker Run completed with detailed evidence",
            level="info",
            detail={"custom_payload": ("timeline payload " * 30) + long_detail_tail},
        )

        response = client.get(f"/sessions/{session_id}", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "compact-text lines-2" in html
    assert "compact-text lines-3" in html
    assert "Full task and launch evidence" in html
    assert "Full launch target" in html
    assert "Full status/result" in html
    assert "Timeline detail" in html
    assert "raw-evidence" in html
    assert "Repo Context Brief" in html
    assert "REPORT_TASK_TAIL_2099" in html
    assert long_command_tail in html
    assert long_detail_tail in html
    assert "custom_payload" in html
    assert long_result_tail in html
    assert repo_tail in html
    assert "opencode" in html
    assert "native_usage" in html
    assert "compact-report-project" in html


def test_session_report_missing_session_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get("/sessions/missing", headers=_portal_headers())

    assert response.status_code == 404
