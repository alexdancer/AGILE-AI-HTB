from agile_ai_htb import db
from tests.portal.helpers import PORTAL_TOKEN, _client, _portal_headers, _project_metadata

def test_settings_workers_page_requires_auth_and_renders_safe_adapter_cards(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        assert client.get("/settings/workers").status_code == 401
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"env": {"OPENAI_API_KEY": "super-secret-key"}},
            supported_models=["5.4"],
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
    assert "Next missing action" in html
    assert "/settings/workers" in html
    assert "Claude Code" in html
    assert "Codex" in html
    assert "OpenCode" in html
    assert "OpenCode diagnostics" in html
    assert "Hermes" not in html
    assert "Adapter identity is the local CLI harness" in html
    assert "Control-plane API keys do not configure native Worker CLI auth" in html
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
    assert "CLI Worker" in page.text
    assert "native_usage, observed_only" in page.text


def test_claude_code_discovery_route_uses_curated_inventory_and_preserves_adapter_context(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.update_worker_adapter(database_path, "codex", is_default=True)
        calls = []

        def fake_discovery_runner(plan):
            calls.append(plan)
            return {"returncode": 0, "stdout": "claude fable\n", "stderr": ""}

        getattr(client.app, "state").worker_model_discovery_runner = fake_discovery_runner
        response = client.post(
            "/settings/workers/claude_code/discover-models",
            headers={**_portal_headers(), "Accept": "text/html"},
            follow_redirects=False,
        )
        page = client.get(response.headers["location"], headers=_portal_headers())

    assert response.status_code == 303
    assert response.headers["location"] == "/settings/workers?adapter_id=claude_code"
    assert calls == []
    assert "Claude Code setup" in page.text
    assert "claude-opus-4-8" in page.text
    assert "claude-opus-4-7" in page.text
    assert "claude-opus-4-6" in page.text
    assert "claude-sonnet-5" in page.text
    assert "claude-sonnet-4-6" in page.text
    assert "claude-haiku-4-5" in page.text
    assert "claude fable" not in page.text
    assert "claude-haiku-4-5-20251001" not in page.text


def test_worker_allowed_models_route_saves_only_discovered_models(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.update_worker_adapter(
            database_path,
            "opencode",
            config={"model_discovery": {"models": ["openai/gpt-5.1", "opencode/big-pickle"]}},
            supported_models=["openai/gpt-5.1"],
        )
        response = client.post(
            "/settings/workers/opencode/allowed-models",
            headers=_portal_headers(),
            data={"allowed_models": "opencode/big-pickle"},
            follow_redirects=False,
        )
        rejected = client.post(
            "/settings/workers/opencode/allowed-models",
            headers=_portal_headers(),
            data={"allowed_models": "undiscovered/model"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert db.get_worker_adapter(database_path, "opencode")["supported_models"] == ["opencode/big-pickle"]
    assert rejected.status_code == 422
    assert db.get_worker_adapter(database_path, "opencode")["supported_models"] == ["opencode/big-pickle"]


def test_workers_page_shows_allowed_model_checkboxes_after_discovery(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.update_worker_adapter(
            database_path,
            "opencode",
            config={"model_discovery": {"models": ["openai/gpt-5.1", "opencode/big-pickle"]}},
            supported_models=["openai/gpt-5.1"],
            is_default=True,
        )
        response = client.get("/settings/workers", headers=_portal_headers())

    assert response.status_code == 200
    assert "/settings/workers/opencode/allowed-models" in response.text
    assert 'data-worker-model-filter' in response.text
    assert "Filter discovered models" in response.text
    assert 'data-worker-model-check-visible' in response.text
    assert "Check visible" in response.text
    assert 'data-worker-model-uncheck-visible' in response.text
    assert "Uncheck visible" in response.text
    assert 'name="allowed_models" value="openai/gpt-5.1" checked' in response.text
    assert 'name="allowed_models" value="opencode/big-pickle"' in response.text

def test_worker_verify_template_error_is_not_reported_as_missing_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.update_worker_adapter(
            database_path,
            "opencode",
            config={"verification_template": ["opencode", "{missing_variable}", "{proxy_url}", "{session_api_key}"]},
            supported_models=["5.4"],
        )
        response = client.post(
            "/settings/workers/opencode/verify",
            headers=_portal_headers(),
            json={"model": "5.4"},
        )

    assert response.status_code == 422
    assert "worker adapter configuration invalid" in response.json()["detail"]
    assert response.json()["detail"] != "worker adapter not found"

def test_board_uses_verified_worker_adapter_status(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        client.post(
            "/tasks",
            json={
                "description": "Launchable estimated task",
                "status": "Estimated",
                "estimate_tokens": 25000,
                "recommended_model": "5.4",
                "metadata": _project_metadata(tmp_path / "harness.db", tmp_path / "connected-project"),
            },
        )
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["5.4"],
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    assert "Launchable estimated task" in response.text
    assert "Launch task" in response.text

def test_configure_route_sets_adapter_default_without_workdir(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.post(
            "/settings/workers/opencode/configure",
            headers=_portal_headers(),
            data={"workdir": str(tmp_path / "my-project"), "is_default": "1"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert response.headers["location"] == "/settings/workers?adapter_id=opencode"
    adapter = db.get_worker_adapter(tmp_path / "harness.db", "opencode")
    assert adapter["workdir"] is None
    assert adapter["is_default"] is True
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
    assert "Claude Code diagnostics" in html or "Codex diagnostics" in html or "OpenCode diagnostics" in html

def test_board_shows_adapter_and_model_selectors(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.create_task(
            database_path,
            description="Test task",
            status="Estimated",
            estimate_tokens=1000,
            recommended_model="5.4",
            metadata=_project_metadata(database_path, tmp_path / "connected-project"),
        )
        response = client.get("/board", headers=_portal_headers())
    assert response.status_code == 200
    html = response.text
    assert "adapter_id" in html
    assert 'name="model"' in html
    assert "Worker Adapter" in html
    assert "Worker model" in html
    assert "selected=5.4" in html
    assert "refreshed" in html

def test_board_does_not_offer_recommended_model_when_adapter_has_no_allowed_models(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.create_task(
            database_path,
            description="No allowed model task",
            status="Estimated",
            estimate_tokens=1000,
            recommended_model="5.4",
            metadata=_project_metadata(database_path, tmp_path / "connected-project"),
        )
        db.update_worker_adapter(
            database_path,
            "codex",
            config={"model_discovery": {"models": ["5.4"]}},
            supported_models=[],
            is_default=True,
        )
        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    assert '<option value="">(no allowed models)</option>' in response.text
    assert "5.4 (no discovered models)" not in response.text

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
            metadata=_project_metadata(database_path, tmp_path / "connected-project"),
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
            recommended_model="5.4",
            metadata=_project_metadata(database_path, tmp_path / "connected-project"),
        )
        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers={**_portal_headers(), "Accept": "text/html"},
            data={"adapter_id": "codex", "model": "5.4"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    location = response.headers["location"]
    assert "error=" in location
    assert response.headers["location"].startswith(f"/projects/{task['metadata']['connected_project_id']}/board?error=")
    board = client.get(
        f"/projects/{task['metadata']['connected_project_id']}/board?error=Worker%20adapter%20is%20not%20configured.",
        headers=_portal_headers(),
    )
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
    assert "launch ready" in html or "setup needed" in html
    assert "Next missing action" in html
    assert "Codex setup" in html
    assert "Choose active adapter" in html
    assert "Advanced details" in html
    assert "CLI Worker" in html
    assert "API / Proxy Worker" in html
    assert "CLI: Observe command only" in html
    assert "Governed via Harness Proxy" not in html
    assert "PROVIDER_API_KEY" not in html


def test_worker_setup_shows_claude_login_diagnostic_in_primary_readiness_copy(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        db.update_worker_adapter(
            database_path,
            "claude_code",
            config={"command": "claude", "allowed_models_configured": True},
            supported_models=["claude-opus-4-8"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            database_path,
            "claude_code",
            verified=False,
            evidence={
                "returncode": 1,
                "stdout": '{"type":"error","message":"Not logged in · Please run /login api_key=abc123"}',
                "stderr": "raw setup output Bearer abc.def",
                "diagnostic": {
                    "code": "claude_code_not_logged_in",
                    "summary": "Not logged in · Please run /login",
                    "next_action": "Run `/login` in Claude Code, then verify the adapter again.",
                    "setup_href": "/settings/workers",
                },
            },
        )

        response = client.get("/settings/workers?adapter_id=claude_code", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Next missing action: Not logged in · Please run /login" in html
    assert "Run `/login` in Claude Code, then verify the adapter again." in html
    assert "Open Worker Setup" in html
    assert "raw setup output" in html
    assert "api_key=abc123" not in html
    assert "Bearer abc.def" not in html
    assert "Advanced details" in html


def test_refresh_diagnostics_route_forces_redetection(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.post(
            "/settings/workers/opencode/refresh-diagnostics",
            headers=_portal_headers(),
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert response.headers["location"] == "/settings/workers?adapter_id=opencode"

