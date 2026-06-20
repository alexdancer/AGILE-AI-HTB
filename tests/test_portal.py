from pathlib import Path

from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.settings import Settings

ROOT = Path(__file__).resolve().parents[1]
PORTAL_TOKEN = "test-portal-token"


class FakeControlPlaneLLM:
    def __init__(self, *, exc: Exception | None = None):
        self.exc = exc
        self.requests = []

    async def acompletion(self, request):
        self.requests.append(request)
        if self.exc:
            raise self.exc
        return {
            "choices": [{"message": {"content": "AGILE_AI_HTB_CONTROL_PLANE_OK"}}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10},
            "api_key": "sk_should_not_render",
        }


def _client(tmp_path):
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    return TestClient(create_app(settings))


def _client_with_control_plane_llm(tmp_path, llm):
    settings = Settings(
        database_path=tmp_path / "harness.db",
        guardrails_path=ROOT / "guardrails.yaml",
        control_plane_model="anthropic/claude-sonnet-4-20250514",
        control_plane_api_key_env="TEST_CONTROL_PLANE_KEY",
    )
    app = create_app(settings)
    app.state.llm_client = llm
    return TestClient(app)


def _portal_headers():
    return {"Authorization": f"Bearer {PORTAL_TOKEN}"}


def test_portal_routes_require_operator_bearer_token(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            json={"task_description": "Secured portal", "model": "claude-haiku"},
        ).json()

        for path in ["/dashboard", "/board", f"/sessions/{started['session_id']}"]:
            assert client.get(path).status_code == 401
            assert client.get(path, headers={"Authorization": "Bearer wrong"}).status_code == 401
            assert client.get(path, headers=_portal_headers()).status_code == 200


def test_portal_login_sets_signed_http_only_cookie_and_logout_clears_it(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        login = client.post("/login", data={"token": PORTAL_TOKEN}, follow_redirects=False)

        assert login.status_code == 303
        assert login.headers["location"] == "/dashboard"
        cookie = login.headers["set-cookie"]
        assert "agile_ai_htb_portal=" in cookie
        assert "HttpOnly" in cookie
        assert "SameSite=lax" in cookie
        assert "Max-Age=43200" in cookie
        assert "Secure" not in cookie

        assert client.get("/dashboard").status_code == 200

        logout = client.post("/logout", follow_redirects=False)
        assert logout.status_code == 303
        assert logout.headers["location"] == "/login"
        assert "agile_ai_htb_portal=\"\"" in logout.headers["set-cookie"]
        assert client.get("/dashboard").status_code == 401


def test_portal_rejects_tampered_or_expired_login_cookie(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        login = client.post("/login", data={"token": PORTAL_TOKEN})
        assert login.status_code == 200
        signed_cookie = client.cookies.get("agile_ai_htb_portal")
        assert signed_cookie is not None

        client.cookies.set("agile_ai_htb_portal", signed_cookie + "tampered")
        assert client.get("/dashboard").status_code == 401

        from agile_ai_htb.auth import sign_portal_cookie

        client.cookies.set("agile_ai_htb_portal", sign_portal_cookie(PORTAL_TOKEN, max_age_seconds=-1))
        assert client.get("/dashboard").status_code == 401


def test_portal_login_rejects_wrong_token(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.post("/login", data={"token": "wrong"})

    assert response.status_code == 401


def test_board_shows_blocked_manual_estimate_state(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        client.post(
            "/tasks",
            json={
                "description": "Needs operator sizing",
                "metadata": {
                    "blocked_reason": "Estimator unavailable: timeout",
                    "requires_manual_estimate": True,
                },
            },
        )
        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    assert "Needs operator sizing" in response.text
    assert "Estimator unavailable: timeout" in response.text
    assert "Manual estimate required" in response.text


def test_dashboard_renders_budget_alarm_and_navigation_sections(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
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
    assert "Daily budget" in html
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


def test_dashboard_budget_ignores_previous_day_usage(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        old = client.post(
            "/session/start",
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


def test_board_renders_columns_and_task_cards(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        created = client.post(
            "/tasks",
            json={
                "description": "Add streaming proxy tests",
                "status": "Estimated",
                "estimate_tokens": 25000,
                "recommended_model": "claude-sonnet",
                "actual_tokens": 12000,
            },
        ).json()
        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    for column in ["Estimated", "Running", "Review", "Done", "Blocked"]:
        assert column in html
    assert "Backlog" not in html
    assert "Other" not in html
    assert "repeat(6," in html
    assert "Add streaming proxy tests" in html
    assert "25,000" in html
    assert "claude-sonnet" in html
    assert "12,000" in html
    assert "Launch task" in html
    assert "adapter_id" in html
    assert created["id"] in html


def test_settings_workers_page_requires_auth_and_renders_safe_adapter_cards(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        assert client.get("/settings/workers").status_code == 401
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"env": {"OPENAI_API_KEY": "super-secret-key"}},
            supported_models=["gpt-5.1-codex"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            tmp_path / "harness.db",
            "codex",
            verified=True,
            evidence={"stdout": "AGILE_AI_HTB_ADAPTER_OK", "env": {"OPENAI_API_KEY": "super-secret-key"}},
        )

        response = client.get("/settings/workers", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Worker adapters" in html
    assert "/settings/workers" in html
    assert "Claude Code" in html
    assert "Codex" in html
    assert "OpenCode" in html
    assert "OpenCode diagnostics" in html
    assert "Hermes" in html
    assert "configured" in html
    assert "unconfigured" in html
    assert "verified" in html
    assert "launchable" in html
    assert "default" in html
    assert "AGILE_AI_HTB_ADAPTER_OK" in html
    assert "super-secret-key" not in html
    assert "OPENAI_API_KEY" not in html
    assert "sk_sess_" not in html


def test_worker_model_discovery_route_uses_native_harness_and_updates_portal(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        calls = []

        def fake_discovery_runner(plan):
            calls.append(plan)
            return {
                "returncode": 0,
                "stdout": '[{"id":"anthropic/claude-sonnet-4"},{"id":"openai/gpt-5.1"}]',
                "stderr": "",
            }

        getattr(client.app, "state").worker_model_discovery_runner = fake_discovery_runner
        response = client.post("/settings/workers/opencode/discover-models", headers=_portal_headers())
        page = client.get("/settings/workers", headers=_portal_headers())

    assert response.status_code == 200
    assert response.json()["models"] == ["anthropic/claude-sonnet-4", "openai/gpt-5.1"]
    assert calls[0].env == {}
    assert "Native model discovery" in page.text
    assert "anthropic/claude-sonnet-4" in page.text
    assert "native, proxy_governed" in page.text


def test_worker_verify_template_error_is_not_reported_as_missing_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.update_worker_adapter(
            database_path,
            "opencode",
            config={"verification_template": ["opencode", "{missing_variable}"]},
            supported_models=["gpt-5.1-codex"],
        )
        response = client.post(
            "/settings/workers/opencode/verify",
            headers=_portal_headers(),
            json={"model": "gpt-5.1-codex"},
        )

    assert response.status_code == 422
    assert "worker adapter configuration invalid" in response.json()["detail"]
    assert response.json()["detail"] != "worker adapter not found"


def test_control_plane_settings_page_separates_control_model_from_worker_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    monkeypatch.setenv("TEST_CONTROL_PLANE_KEY", "sk_should_not_render")
    with _client_with_control_plane_llm(tmp_path, FakeControlPlaneLLM()) as client:
        response = client.get("/settings/control-plane", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Control plane model" in html
    assert "anthropic/claude-sonnet-4-20250514" in html
    assert "TEST_CONTROL_PLANE_KEY" in html
    assert "AGILE-AI-HTB orchestration model" in html
    assert "Worker Harness" in html
    assert "sk_should_not_render" not in html


def test_control_plane_connection_test_records_sanitized_status(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeControlPlaneLLM()
    with _client_with_control_plane_llm(tmp_path, llm) as client:
        response = client.post("/settings/control-plane/test", headers=_portal_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["status"]["online"] is True
    assert body["status"]["details"]["model"] == "anthropic/claude-sonnet-4-20250514"
    assert body["status"]["details"]["usage"]["total_tokens"] == 10
    assert "sk_should_not_render" not in str(body)
    assert llm.requests[0]["model"] == "anthropic/claude-sonnet-4-20250514"


def test_control_plane_connection_failure_records_no_secret_values(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeControlPlaneLLM(exc=RuntimeError("secret sk_bad_key"))
    with _client_with_control_plane_llm(tmp_path, llm) as client:
        response = client.post("/settings/control-plane/test", headers=_portal_headers())

    assert response.status_code == 503
    body = response.json()
    assert body["passed"] is False
    assert body["status"]["online"] is False
    assert "sk_bad_key" not in str(body)
    assert "***REDACTED***" in body["status"]["details"]["error"]


def test_board_uses_verified_worker_adapter_status(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        client.post(
            "/tasks",
            json={
                "description": "Launchable estimated task",
                "status": "Estimated",
                "estimate_tokens": 25000,
                "recommended_model": "gpt-5.1-codex",
            },
        )
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.1-codex"],
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    assert "Launchable estimated task" in response.text
    assert "Launch task" in response.text


def test_board_renders_unexpected_statuses_as_blocked(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        client.post("/tasks", json={"description": "Odd status task", "status": "Legacy Backlog"})
        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    assert "Blocked" in response.text
    assert "Other" not in response.text
    assert "Odd status task" in response.text
    assert "Unsupported task status: Legacy Backlog" in response.text


def test_sessions_index_renders_mockup_style_session_table(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
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
    assert "Review live portal" in html
    assert "100" in html
    assert "zone:" in html


def test_alarms_browser_accept_renders_html_inbox_without_breaking_json_api(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
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


def test_session_report_renders_totals_alarm_checkpoint_without_internal_artifact_link(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
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

        response = client.get(f"/sessions/{session_id}", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Audit session" in html
    assert "500" in html
    assert "yellow" in html
    assert "CHECKPOINT_FAIL" in html
    assert "budget_health" in html
    assert "Requires review" in html
    assert f"/session/{session_id}/artifact" not in html
    assert "session_key_hash" not in html
    assert "guardrail_overrides" not in html


def test_session_report_missing_session_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get("/sessions/missing", headers=_portal_headers())

    assert response.status_code == 404


# ── Adapter configuration workflow tests ──

def test_configure_route_sets_workdir(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.post(
            "/settings/workers/opencode/configure",
            headers=_portal_headers(),
            data={"workdir": str(tmp_path / "my-project")},
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert response.headers["location"] == "/settings/workers"
    adapter = db.get_worker_adapter(tmp_path / "harness.db", "opencode")
    assert adapter["workdir"] == str(tmp_path / "my-project")
    assert adapter["configured"] is True


def test_configure_route_sets_default_and_clears_previous(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        # Set opencode as default
        client.post(
            "/settings/workers/opencode/configure",
            headers=_portal_headers(),
            data={"workdir": str(tmp_path), "is_default": "1"},
        )
        # Set codex as default - should clear opencode
        client.post(
            "/settings/workers/codex/configure",
            headers=_portal_headers(),
            data={"workdir": str(tmp_path), "is_default": "1"},
        )
    assert db.get_worker_adapter(database_path, "opencode")["is_default"] is False
    assert db.get_worker_adapter(database_path, "codex")["is_default"] is True


def test_workers_page_shows_diagnostics_for_all_adapters(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get("/settings/workers", headers=_portal_headers())
    assert response.status_code == 200
    html = response.text
    assert "Claude Code diagnostics" in html or "Codex diagnostics" in html or "Hermes diagnostics" in html


def test_board_shows_adapter_and_model_selectors(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.create_task(
            database_path,
            description="Test task",
            status="Estimated",
            estimate_tokens=1000,
            recommended_model="gpt-5.1-codex",
        )
        response = client.get("/board", headers=_portal_headers())
    assert response.status_code == 200
    html = response.text
    assert "adapter_id" in html
    assert 'name="model"' in html


def test_board_launch_button_visible_without_verified_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.create_task(
            database_path,
            description="Unverified launch test",
            status="Estimated",
            estimate_tokens=500,
            recommended_model="claude-sonnet",
        )
        response = client.get("/board", headers=_portal_headers())
    assert response.status_code == 200
    assert "Launch task" in response.text


def test_launch_unverified_adapter_shows_error_banner(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        task = db.create_task(
            database_path,
            description="Will fail launch",
            status="Estimated",
            estimate_tokens=500,
            recommended_model="gpt-5.1-codex",
        )
        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers={**_portal_headers(), "Accept": "text/html"},
            data={"adapter_id": "codex", "model": "gpt-5.1-codex"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    location = response.headers["location"]
    assert "error=" in location
    assert response.headers["location"].startswith("/board?error=")
    board = client.get("/board?error=Worker%20adapter%20is%20not%20configured.", headers=_portal_headers())
    assert "Open Worker Setup" in board.text
    assert "/settings/workers" in board.text


def test_guided_worker_setup_selects_default_adapter_and_keeps_advanced_details(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.update_worker_adapter(database_path, "codex", workdir=str(tmp_path), config={"command": "codex"}, is_default=True)
        response = client.get("/settings/workers", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Codex setup" in html
    assert "Choose active adapter" in html
    assert "Advanced details" in html
    assert "Proxy-governed direct provider usage" in html
    assert "PROVIDER_API_KEY" not in html


def test_refresh_diagnostics_route_forces_redetection(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.post(
            "/settings/workers/opencode/refresh-diagnostics",
            headers=_portal_headers(),
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert response.headers["location"] == "/settings/workers"


def test_setup_overview_and_budget_settings_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        setup = client.get("/setup", headers=_portal_headers())
        assert setup.status_code == 200
        assert "First-run setup" in setup.text
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
    assert db.get_token_budget_settings(tmp_path / "harness.db") == {
        "confirmed": True,
        "daily_cap_tokens": 999000,
        "session_cap_tokens": 111000,
    }


def test_saved_budget_gates_launch_and_is_carried_to_session(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.set_token_budget_settings(database_path, daily_cap_tokens=1000, session_cap_tokens=700)
        db.update_worker_adapter(
            database_path,
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.1-codex"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(database_path, "codex", verified=True, evidence={"ok": True})
        blocked = db.create_task(
            database_path,
            description="Too large for saved budget",
            status="Estimated",
            estimate_tokens=1200,
            recommended_model="gpt-5.1-codex",
        )
        ok = db.create_task(
            database_path,
            description="Within saved budget",
            status="Estimated",
            estimate_tokens=500,
            recommended_model="gpt-5.1-codex",
        )
        blocked_response = client.post(
            f"/tasks/{blocked['id']}/launch",
            headers=_portal_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.1-codex"},
        )

        def fake_runner(plan):
            return {"returncode": 0, "stdout": "", "stderr": ""}

        getattr(client.app, "state").task_launch_runner = fake_runner
        launched = client.post(
            f"/tasks/{ok['id']}/launch",
            headers=_portal_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.1-codex"},
        )

    assert blocked_response.status_code == 409
    assert "Task estimate exceeds remaining launch budget." in str(blocked_response.json())
    assert launched.status_code == 200
    session = launched.json()["session"]
    assert session["guardrail_overrides"]["budget"]["daily_cap_tokens"] == 1000
    assert session["guardrail_overrides"]["budget"]["session_cap_tokens"] == 700
