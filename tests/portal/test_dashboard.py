from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.settings import Settings
from tests.portal.helpers import ROOT, PORTAL_TOKEN, _client, _portal_headers

def test_dashboard_renders_budget_alarm_and_navigation_sections(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": "Build portal", "model": "claude-haiku"},
        ).json()
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=started["session_id"],
            model="claude-haiku",
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01,
            raw_usage={"total_tokens": 150},
        )
        db.record_alarm(
            tmp_path / "harness.db",
            session_id=started["session_id"],
            alarm={
                "id": "alarm-dashboard-1",
                "type": "BUDGET_YELLOW",
                "severity": "LOW",
                "context": {},
                "recommended_action": "Review spend.",
            },
        )

        response = client.get("/dashboard", headers=_portal_headers())

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    assert "Daily governed budget" in html
    assert "Operator next actions" in html
    assert "Set up Worker adapter" in html
    assert 'href="/settings/workers"' in html
    assert "Review 1 open alarm" in html
    assert 'href="/alarms"' in html
    assert "Open task board" in html
    assert 'href="/board"' in html
    assert "150" in html
    assert "Sessions" in html
    assert "Alarms" in html
    assert "Task board" in html
    assert "Active sessions" in html
    assert started["session_id"] in html
    assert "Build portal" in html
    assert "AGILE-AI-HTB" in html
    assert "live harness" in html
    assert "https://unpkg.com/htmx.org" not in html
    assert "https://cdn.jsdelivr.net/npm/chart.js" not in html
    assert "PROVIDER_API_KEY" not in html
    assert "sk_sess_" not in html

def test_dashboard_next_actions_count_launch_and_review_tasks(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        client.post(
            "/tasks",
            json={
                "description": "Ready launch task",
                "status": "Estimated",
                "estimate_tokens": 1000,
                "recommended_model": "gpt-5.1-codex",
            },
        )
        session = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": "Completed Worker task", "model": "gpt-5.1-codex"},
        ).json()
        db.update_session_status(database_path, session["session_id"], "completed")
        client.post(
            "/tasks",
            json={
                "description": "Needs review",
                "status": "Review",
                "estimate_tokens": 1000,
                "recommended_model": "gpt-5.1-codex",
                "session_id": session["session_id"],
            },
        )

        response = client.get("/dashboard", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Launch 1 estimated task" in html
    assert "Review 1 task" in html
    assert html.count('href="/board"') >= 3

def test_dashboard_next_actions_hide_worker_setup_when_adapter_launchable(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.update_worker_adapter(
            database_path,
            "opencode",
            workdir=str(tmp_path),
            config={"native_launch_template": ["opencode", "run"]},
            supported_models=["openai/gpt-5.1"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            database_path,
            "opencode",
            verified=True,
            evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
        )

        response = client.get("/dashboard", headers=_portal_headers())

    assert response.status_code == 200
    assert "Set up Worker adapter" not in response.text
    assert "Open task board" in response.text

def test_dashboard_next_actions_prioritize_critical_alarms(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        session = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": "Budget alarm", "model": "claude-haiku"},
        ).json()
        db.record_alarm(
            database_path,
            session_id=session["session_id"],
            alarm={
                "id": "critical-dashboard-alarm",
                "type": "DAILY_CAP_EXCEEDED",
                "severity": "HIGH",
                "context": {},
                "recommended_action": "Stop launches.",
            },
        )

        response = client.get("/dashboard", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Handle 1 critical alarm" in html
    assert "Review 1 open alarm" not in html
    assert 'href="/alarms"' in html

def test_dashboard_budget_ignores_previous_day_usage(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        old = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": "Old spend", "model": "claude-haiku"},
        ).json()
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=old["session_id"],
            model="claude-haiku",
            prompt_tokens=999000,
            completion_tokens=0,
            cost=0,
            raw_usage={"total_tokens": 999000},
        )
        with db.connect(tmp_path / "harness.db") as conn:
            conn.execute("update token_turns set created_at = ?", ("2000-01-01T00:00:00+00:00",))

        current = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": "Current spend", "model": "claude-haiku"},
        ).json()
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=current["session_id"],
            model="claude-haiku",
            prompt_tokens=10,
            completion_tokens=5,
            cost=0,
            raw_usage={"total_tokens": 15},
        )

        response = client.get("/dashboard", headers=_portal_headers())

    assert response.status_code == 200
    assert "999,000" not in response.text
    assert "15" in response.text


def test_dashboard_daily_budget_counts_agent_review_reporting_tokens(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.set_token_budget_settings(database_path, daily_cap_tokens=1000, session_cap_tokens=500)
        review_session = db.create_session(
            database_path,
            task_description="Agent Review spend",
            model="control-plane",
            session_key_hash="r" * 64,
            guardrail_overrides={"spend_category": "agent_review"},
            status="completed",
        )
        db.record_token_turn(
            database_path,
            session_id=review_session["id"],
            usage_kind="reporting",
            model="control-plane",
            prompt_tokens=900,
            completion_tokens=0,
            cost=0,
            raw_usage={
                "total_tokens": 900,
                "spend_category": "reporting_summary",
                "usage_source": "control_plane",
                "reporting_kind": "agent_review",
            },
        )
        db.record_token_turn(
            database_path,
            session_id=review_session["id"],
            usage_kind="estimation",
            model="control-plane",
            prompt_tokens=50,
            completion_tokens=0,
            cost=0,
            raw_usage={"total_tokens": 50},
        )

        response = client.get("/dashboard", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Daily governed budget" in html
    assert "950 / 1,000" in html
    assert "zone: red" in html
    assert "Agent Review/reporting 900" in html
    assert "Planning/estimation 50" in html


def test_dashboard_shows_accuracy_with_enough_completed_tasks(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    db.init_db(settings.database_path)
    app = create_app(settings)

    # Create 3 completed tasks with estimates and actuals
    for est, act in [(500, 550), (300, 280), (1000, 1400)]:
        db.create_task(
            settings.database_path,
            description=f"Task est={est}",
            status="Done",
            estimate_tokens=est,
            actual_tokens=act,
        )

    with TestClient(app) as client:
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {PORTAL_TOKEN}"})
    assert response.status_code == 200
    html = response.text
    assert "Estimation accuracy" in html
    assert "3" in html  # completed count


def test_dashboard_shows_placeholder_with_insufficient_completed_tasks(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    db.init_db(settings.database_path)
    app = create_app(settings)

    # Only 1 completed task
    db.create_task(
        settings.database_path,
        description="Task 1",
        status="Done",
        estimate_tokens=500,
        actual_tokens=550,
    )

    with TestClient(app) as client:
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {PORTAL_TOKEN}"})
    assert response.status_code == 200
    html = response.text
    assert "Not enough completed tasks for accuracy tracking" in html

