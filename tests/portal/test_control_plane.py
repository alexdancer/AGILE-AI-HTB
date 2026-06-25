import os
from pathlib import Path

from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.operator_config import CONTROL_API_KEY_PLACEHOLDER, load_operator_config
from agile_ai_htb.project_context import project_task_metadata
from agile_ai_htb.settings import Settings

ROOT = Path(__file__).resolve().parents[2]
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


def _client_with_control_plane_llm(tmp_path, llm, *, control_plane_model="anthropic/claude-sonnet-4-20250514"):
    settings = Settings(
        database_path=tmp_path / "harness.db",
        guardrails_path=ROOT / "guardrails.yaml",
        control_plane_model=control_plane_model,
        control_plane_api_key_env="TEST_CONTROL_PLANE_KEY",
    )
    app = create_app(settings)
    app.state.llm_client = llm
    return TestClient(app)


def _portal_headers():
    return {"Authorization": f"Bearer {PORTAL_TOKEN}"}


def _connect_project(database_path: Path, root: Path) -> dict:
    root.mkdir(exist_ok=True)
    return db.upsert_connected_project(
        database_path,
        name=root.name,
        root_path=str(root.resolve()),
        profile={"name": root.name, "root_path": str(root.resolve()), "test_command": "pytest"},
        capability={"state": "launch_ready", "can_launch": True},
    )


def _project_metadata(database_path: Path, root: Path) -> dict:
    return project_task_metadata(_connect_project(database_path, root))

def test_control_plane_save_persists_and_hot_swaps_settings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    for name in [
        "AGILE_AI_HTB_CONTROL_PROVIDER",
        "AGILE_AI_HTB_CONTROL_MODEL",
        "AGILE_AI_HTB_CONTROL_BASE_URL",
        "AGILE_AI_HTB_CONTROL_API_KEY_ENV",
        "AGILE_AI_HTB_ESTIMATOR_MODEL",
        "AGILE_AI_HTB_TASK_BREAKDOWN_MODEL",
    ]:
        monkeypatch.delenv(name, raising=False)

    class CapturingLLM:
        def __init__(self, settings):
            self.settings = settings
            self.requests = []

        async def acompletion(self, request):
            self.requests.append(request)
            return {"choices": [{"message": {"content": "AGILE_AI_HTB_CONTROL_PLANE_OK"}}]}

    from agile_ai_htb.routes import portal

    monkeypatch.setattr(portal, "LLMClient", CapturingLLM)
    app = create_app(Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml"))
    with TestClient(app) as client:
        response = client.post(
            "/settings/control-plane",
            headers=_portal_headers(),
            json={
                "control_plane_provider": "anthropic",
                "control_plane_model": "claude-haiku-4-5",
                "control_plane_base_url": "",
                "control_plane_api_key_env": "ANTHROPIC_API_KEY",
                "apply_to_estimator_breakdown": True,
            },
        )
        test_response = client.post("/settings/control-plane/test", headers=_portal_headers())
        app_settings = app.state.settings
        llm = app.state.llm_client

    assert response.status_code == 200
    body = response.json()
    assert body["settings"]["control_plane_provider"] == "anthropic"
    assert body["settings"]["control_plane_model"] == "claude-haiku-4-5"
    assert body["settings"]["estimator_model"] == "claude-haiku-4-5"
    assert body["settings"]["task_breakdown_model"] == "claude-haiku-4-5"
    assert body["status"]["online"] is False
    assert body["status"]["details"]["status"] == "needs_test"
    assert app_settings.control_plane_api_key_env == "ANTHROPIC_API_KEY"
    assert llm.settings.control_plane_model == "claude-haiku-4-5"
    assert test_response.status_code == 200
    assert llm.requests[0]["model"] == "claude-haiku-4-5"
    config = load_operator_config(tmp_path / ".htb" / "config.toml")
    assert config["control_plane_provider"] == "anthropic"
    assert config["control_plane_model"] == "claude-haiku-4-5"
    assert config["estimator_model"] == "claude-haiku-4-5"
    assert config["task_breakdown_model"] == "claude-haiku-4-5"
    assert config["control_plane_api_key_env"] == "ANTHROPIC_API_KEY"
    secrets_text = (tmp_path / ".htb" / "secrets.env").read_text(encoding="utf-8")
    assert "ANTHROPIC_API_KEY" in secrets_text
    assert CONTROL_API_KEY_PLACEHOLDER in secrets_text

def test_control_plane_save_updates_bootstrap_env_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    monkeypatch.setenv("AGILE_AI_HTB_CONTROL_PROVIDER", "openai")
    monkeypatch.setenv("AGILE_AI_HTB_CONTROL_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("AGILE_AI_HTB_CONTROL_API_KEY_ENV", "AGILE_AI_HTB_CONTROL_API_KEY")

    app = create_app(Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml"))
    with TestClient(app) as client:
        response = client.post(
            "/settings/control-plane",
            headers=_portal_headers(),
            json={
                "control_plane_provider": "openai",
                "control_plane_model": "gpt-5.5",
                "control_plane_base_url": "",
                "control_plane_api_key_env": "AGILE_AI_HTB_CONTROL_API_KEY",
                "apply_to_estimator_breakdown": True,
            },
        )

    assert response.status_code == 200
    assert response.json()["settings"]["control_plane_model"] == "gpt-5.5"
    assert app.state.settings.control_plane_model == "gpt-5.5"
    assert app.state.settings.estimator_model == "gpt-5.5"
    assert os.environ["AGILE_AI_HTB_CONTROL_MODEL"] == "gpt-5.5"
    assert load_operator_config(tmp_path / ".htb" / "config.toml")["control_plane_model"] == "gpt-5.5"

def test_control_plane_save_loads_existing_secret_env_for_new_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    monkeypatch.delenv("NEW_CONTROL_KEY", raising=False)
    secrets_path = tmp_path / ".htb" / "secrets.env"
    secrets_path.parent.mkdir()
    secrets_path.write_text("NEW_CONTROL_KEY='real-test-key'\n", encoding="utf-8")

    app = create_app(Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml"))
    with TestClient(app) as client:
        response = client.post(
            "/settings/control-plane",
            headers=_portal_headers(),
            json={
                "control_plane_provider": "openai",
                "control_plane_model": "gpt-5.4-mini",
                "control_plane_base_url": "",
                "control_plane_api_key_env": "NEW_CONTROL_KEY",
            },
        )

    assert response.status_code == 200
    assert os.getenv("NEW_CONTROL_KEY") == "real-test-key"

def test_control_plane_save_rejects_blank_model_and_invalid_base_url(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        blank_model = client.post(
            "/settings/control-plane",
            headers=_portal_headers(),
            json={
                "control_plane_provider": "openai",
                "control_plane_model": "   ",
                "control_plane_base_url": "",
                "control_plane_api_key_env": "OPENAI_API_KEY",
            },
        )
        invalid_base_url = client.post(
            "/settings/control-plane",
            headers=_portal_headers(),
            json={
                "control_plane_provider": "openai-compatible",
                "control_plane_model": "custom-model",
                "control_plane_base_url": "not a url",
                "control_plane_api_key_env": "COMPATIBLE_API_KEY",
            },
        )
        missing_base_url = client.post(
            "/settings/control-plane",
            headers=_portal_headers(),
            json={
                "control_plane_provider": "openai-compatible",
                "control_plane_model": "custom-model",
                "control_plane_base_url": "",
                "control_plane_api_key_env": "COMPATIBLE_API_KEY",
            },
        )

    assert blank_model.status_code == 422
    assert invalid_base_url.status_code == 422
    assert missing_base_url.status_code == 422

def test_control_plane_save_failure_keeps_running_settings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    from agile_ai_htb.routes import portal

    def fail_write(**_updates):
        raise OSError("disk full")

    monkeypatch.setattr(portal, "update_operator_config", fail_write)
    app = create_app(Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml"))
    with TestClient(app) as client:
        before = app.state.settings
        response = client.post(
            "/settings/control-plane",
            headers=_portal_headers(),
            json={
                "control_plane_provider": "anthropic",
                "control_plane_model": "claude-haiku-4-5",
                "control_plane_base_url": "",
                "control_plane_api_key_env": "ANTHROPIC_API_KEY",
            },
        )
        after = app.state.settings

    assert response.status_code == 500
    assert before is after
    assert after.control_plane_model != "claude-haiku-4-5"

def test_control_plane_settings_page_shows_presets_and_needs_test(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    db.upsert_execution_backend_status(
        database_path,
        "control_plane_model",
        name="Control Plane Model",
        online=False,
        details={"status": "needs_test", "reason": "configuration changed; test required"},
    )
    with _client(tmp_path) as client:
        response = client.get("/settings/control-plane", headers=_portal_headers())
        setup = client.get("/setup", headers=_portal_headers())

    assert response.status_code == 200
    assert "gpt-5.4-mini" in response.text
    assert "gpt-5.5" in response.text
    assert 'list="control-plane-model-options"' in response.text
    assert "claude-haiku-4-5" in response.text
    assert "Save control-plane model" in response.text
    assert "needs test" in response.text
    assert "needs test" in setup.text

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

def test_control_plane_connection_test_does_not_cap_gpt5_smoke_response(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeControlPlaneLLM()
    with _client_with_control_plane_llm(tmp_path, llm, control_plane_model="gpt-5.4-mini") as client:
        response = client.post("/settings/control-plane/test", headers=_portal_headers())

    assert response.status_code == 200
    assert llm.requests[0]["model"] == "gpt-5.4-mini"
    assert "max_tokens" not in llm.requests[0]
    assert "max_completion_tokens" not in llm.requests[0]

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

