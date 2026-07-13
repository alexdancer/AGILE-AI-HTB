from agile_ai_htb import db
from tests.portal.helpers import PORTAL_TOKEN, _client, _connect_project, _portal_headers, _project_metadata


class _CapabilityBackend:
    def __init__(self, state: str):
        self.state = state

    def project_capability(self, project):
        return {
            "state": self.state,
            "label": self.state.replace("_", "-").title(),
            "backend": "test_backend",
            "reasons": [],
            "can_launch": self.state == "launch_ready",
            "can_analyze": self.state in {"analysis_ready", "launch_ready"},
        }


def _prepare_ready_setup(database_path, workdir, monkeypatch):
    monkeypatch.setenv("AGILE_AI_HTB_CONTROL_API_KEY", "test-control-plane-key")
    db.set_token_budget_settings(database_path, daily_cap_tokens=999000, session_cap_tokens=111000)
    db.update_worker_adapter(
        database_path,
        "codex",
        workdir=str(workdir),
        config={"command": "codex"},
        supported_models=["gpt-5.4"],
        is_default=True,
    )
    db.mark_worker_adapter_verification(
        database_path,
        "codex",
        verified=True,
        evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
    )


def _connect_invalid_project(database_path, root_path):
    return db.upsert_connected_project(
        database_path,
        name=root_path.name,
        root_path=str(root_path),
        profile={"name": root_path.name, "root_path": str(root_path)},
        capability={"state": "launch_ready", "can_launch": True},
    )


def test_setup_requires_connected_project_after_other_requirements_pass(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"

    with _client(tmp_path) as client:
        _prepare_ready_setup(database_path, tmp_path, monkeypatch)
        setup = client.get("/setup", headers=_portal_headers())

    assert setup.status_code == 200
    assert "next missing action" in setup.text
    assert 'href="/settings/project">Open Projects</a>' in setup.text
    assert "Governed Worker launch is ready." not in setup.text
    assert "Projects</a>: needs setup" in setup.text


def test_setup_defensively_rejects_analysis_ready_project(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"

    with _client(tmp_path) as client:
        _prepare_ready_setup(database_path, tmp_path, monkeypatch)
        _connect_project(database_path, tmp_path / "analysis-project")
        getattr(client.app, "state").execution_backend = _CapabilityBackend("analysis_ready")
        setup = client.get("/setup", headers=_portal_headers())

    assert setup.status_code == 200
    assert 'href="/settings/project">Open Projects</a>' in setup.text
    assert "Projects</a>: needs setup" in setup.text
    assert "Governed Worker launch is ready." not in setup.text


def test_setup_rejects_blocked_project_and_preserves_earlier_blocker_priority(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"

    with _client(tmp_path) as client:
        _prepare_ready_setup(database_path, tmp_path, monkeypatch)
        _connect_invalid_project(database_path, tmp_path / "missing-project")
        blocked = client.get("/setup", headers=_portal_headers())
        monkeypatch.delenv("AGILE_AI_HTB_CONTROL_API_KEY")
        earlier_blocker = client.get("/setup", headers=_portal_headers())

    assert blocked.status_code == 200
    assert 'href="/settings/project">Open Projects</a>' in blocked.text
    assert "Projects</a>: needs setup" in blocked.text
    assert 'href="/settings/control-plane">Open Control plane model</a>' in earlier_blocker.text
    assert "Projects</a>: needs setup" in earlier_blocker.text


def test_setup_links_exact_launch_ready_project_board(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"

    with _client(tmp_path) as client:
        _prepare_ready_setup(database_path, tmp_path, monkeypatch)
        launch_ready = _connect_project(database_path, tmp_path / "launch-ready-project")
        _connect_invalid_project(database_path, tmp_path / "newer-blocked-project")
        setup = client.get("/setup", headers=_portal_headers())

    expected_href = f'/projects/{launch_ready["id"]}/board'
    assert setup.status_code == 200
    assert "Governed Worker launch is ready." in setup.text
    assert f'href="{expected_href}"' in setup.text
    assert 'href="/board"' not in setup.text


def test_setup_ignores_stale_launch_ready_capability_when_local_runner_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"

    with _client(tmp_path, local_runner_enabled=False) as client:
        _prepare_ready_setup(database_path, tmp_path, monkeypatch)
        _connect_project(database_path, tmp_path / "stale-launch-ready-project")
        setup = client.get("/setup", headers=_portal_headers())

    assert setup.status_code == 200
    assert 'href="/settings/project">Open Projects</a>' in setup.text
    assert "Projects</a>: needs setup" in setup.text
    assert "Governed Worker launch is ready." not in setup.text

def test_setup_overview_and_budget_settings_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        setup = client.get("/setup", headers=_portal_headers())
        assert setup.status_code == 200
        assert "First-run setup" in setup.text
        assert "next missing action" in setup.text
        assert "Open Control plane model" in setup.text
        assert "Token budget" in setup.text

        saved = client.post(
            "/settings/budget",
            headers={**_portal_headers(), "Accept": "text/html"},
            data={"daily_cap_tokens": "999000", "session_cap_tokens": "111000"},
            follow_redirects=False,
        )
        assert saved.status_code == 303
        assert saved.headers["location"] == "/setup"
        page = client.get("/settings/budget", headers=_portal_headers())

    assert page.status_code == 200
    assert 'value="999000"' in page.text
    assert 'value="111000"' in page.text
    assert "Daily governed model-spend cap" in page.text
    assert "Agent Review" in page.text
    assert "control_plane" in page.text
    assert "worker_execution" in page.text
    assert db.get_token_budget_settings(tmp_path / "harness.db") == {
        "confirmed": True,
        "daily_cap_tokens": 999000,
        "session_cap_tokens": 111000,
    }


def test_budget_reset_route_preserves_settings_and_renders_counter_copy(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.set_token_budget_settings(database_path, daily_cap_tokens=1000, session_cap_tokens=700)

        reset = client.post(
            "/settings/budget/reset",
            headers={**_portal_headers(), "Accept": "text/html"},
            follow_redirects=False,
        )
        page = client.get("/settings/budget", headers=_portal_headers())

    saved = db.get_token_budget_settings(database_path)
    assert reset.status_code == 303
    assert reset.headers["location"] == "/settings/budget"
    assert saved["daily_cap_tokens"] == 1000
    assert saved["session_cap_tokens"] == 700
    assert saved["daily_usage_reset_at"]
    assert "Today’s budget counter" in page.text
    assert "Reset today’s budget counter" in page.text
    assert "Token ledger evidence, session reports, and task actuals are preserved." in page.text


def test_budget_reset_allows_launch_after_pre_reset_daily_spend(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        _connect_project(database_path, tmp_path / "connected-project")
        db.set_token_budget_settings(database_path, daily_cap_tokens=1000, session_cap_tokens=700)
        prior_session = db.create_session(
            database_path,
            task_description="Spend before soft reset",
            model="claude-haiku",
            session_key_hash="hash-pre-reset",
            guardrail_overrides={},
            status="completed",
        )
        db.record_token_turn(
            database_path,
            session_id=prior_session["id"],
            model="claude-haiku",
            prompt_tokens=900,
            completion_tokens=0,
            cost=0.0,
            raw_usage={"total_tokens": 900, "spend_category": "worker_execution"},
        )
        with db.connect(database_path) as conn:
            conn.execute("update token_turns set created_at = ?", (db.current_day_start_iso("local"),))

        reset = client.post("/settings/budget/reset", headers=_portal_headers())
        task = db.create_task(
            database_path,
            description="Within reset daily window",
            status="Estimated",
            estimate_tokens=500,
            recommended_model="gpt-5.4",
            metadata=_project_metadata(database_path, tmp_path / "connected-project"),
        )
        db.update_worker_adapter(
            database_path,
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(database_path, "codex", verified=True, evidence={"ok": True})

        def fake_runner(plan):
            return {"returncode": 0, "stdout": "", "stderr": ""}

        getattr(client.app, "state").task_launch_runner = fake_runner
        launched = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_portal_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.4"},
        )

    assert reset.status_code == 200
    assert launched.status_code == 200
    assert len(db.build_session_artifact(database_path, prior_session["id"])["token_log"]) == 1
    launch_budget = launched.json()["session"]["guardrail_overrides"]["budget"]
    assert launch_budget["budget_since"] == db.get_token_budget_settings(database_path)["daily_usage_reset_at"]


def test_saved_budget_gates_launch_and_is_carried_to_session(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        _connect_project(database_path, tmp_path / "connected-project")
        db.set_token_budget_settings(database_path, daily_cap_tokens=1000, session_cap_tokens=700)
        db.update_worker_adapter(
            database_path,
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(database_path, "codex", verified=True, evidence={"ok": True})
        project_metadata = _project_metadata(database_path, tmp_path / "connected-project")
        blocked = db.create_task(
            database_path,
            description="Too large for saved budget",
            status="Estimated",
            estimate_tokens=1200,
            recommended_model="gpt-5.4",
            metadata=project_metadata,
        )
        ok = db.create_task(
            database_path,
            description="Within saved budget",
            status="Estimated",
            estimate_tokens=500,
            recommended_model="gpt-5.4",
            metadata=project_metadata,
        )
        blocked_response = client.post(
            f"/tasks/{blocked['id']}/launch",
            headers=_portal_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.4"},
        )

        def fake_runner(plan):
            return {"returncode": 0, "stdout": "", "stderr": ""}

        getattr(client.app, "state").task_launch_runner = fake_runner
        launched = client.post(
            f"/tasks/{ok['id']}/launch",
            headers=_portal_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.4"},
        )

    assert blocked_response.status_code == 409
    assert "Task estimate exceeds remaining launch budget." in str(blocked_response.json())
    assert launched.status_code == 200
    session = launched.json()["session"]
    assert session["guardrail_overrides"]["budget"]["daily_cap_tokens"] == 1000
    assert session["guardrail_overrides"]["budget"]["session_cap_tokens"] == 700

