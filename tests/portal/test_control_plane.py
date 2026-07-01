import os
import re

from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.operator_config import CONTROL_API_KEY_PLACEHOLDER, load_operator_config
from agile_ai_htb.settings import Settings
from tests.portal.helpers import (
    ROOT,
    PORTAL_TOKEN,
    FakeControlPlaneLLM,
    _client,
    _client_with_control_plane_llm,
    _portal_headers,
)


def _model_option(html: str, value: str) -> str:
    match = re.search(rf'<option value="{re.escape(value)}"[^>]*>', html)
    assert match, value
    return match.group(0)


def _assert_selectable(option: str) -> None:
    assert "hidden" not in option
    assert "disabled" not in option


def _assert_not_selectable(option: str) -> None:
    assert "hidden" in option
    assert "disabled" in option

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


def test_control_plane_save_writes_submitted_api_key_without_config_leak(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

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
                "control_plane_api_key": "DEMO_KEY_VALUE_999",
            },
        )
        page = client.get("/settings/control-plane", headers=_portal_headers())

    assert response.status_code == 200
    assert os.getenv("ANTHROPIC_API_KEY") == "DEMO_KEY_VALUE_999"
    config_text = (tmp_path / ".htb" / "config.toml").read_text(encoding="utf-8")
    secrets_text = (tmp_path / ".htb" / "secrets.env").read_text(encoding="utf-8")
    assert "DEMO_KEY_VALUE_999" not in config_text
    assert "ANTHROPIC_API_KEY=DEMO_KEY_VALUE_999" in secrets_text
    assert "DEMO_KEY_VALUE_999" not in str(response.json())
    assert "DEMO_KEY_VALUE_999" not in page.text
    assert "API key present</div><div class=\"v\">yes" in page.text


def test_control_plane_blank_api_key_preserves_existing_secret(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    secrets_path = tmp_path / ".htb" / "secrets.env"
    secrets_path.parent.mkdir()
    secrets_path.write_text("ANTHROPIC_API_KEY='DEMO_KEY_VALUE_999'\n", encoding="utf-8")

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
                "control_plane_api_key": "",
            },
        )

    text = secrets_path.read_text(encoding="utf-8")
    assert response.status_code == 200
    assert "DEMO_KEY_VALUE_999" in text
    assert CONTROL_API_KEY_PLACEHOLDER not in text
    assert os.getenv("ANTHROPIC_API_KEY") == "DEMO_KEY_VALUE_999"

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
                "control_plane_api_key": "DEMO_SECRET_VALUE_999",
            },
        )
        unresolved_custom = client.post(
            "/settings/control-plane",
            headers=_portal_headers(),
            json={
                "control_plane_provider": "openai-compatible",
                "control_plane_model": "__custom__",
                "control_plane_base_url": "https://example.invalid/v1",
                "control_plane_api_key_env": "COMPATIBLE_API_KEY",
            },
        )

    assert blank_model.status_code == 422
    assert invalid_base_url.status_code == 422
    assert missing_base_url.status_code == 422
    assert unresolved_custom.status_code == 422
    assert "DEMO_SECRET_VALUE_999" not in missing_base_url.text
    assert all("input" not in detail for detail in missing_base_url.json()["detail"])

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
    monkeypatch.chdir(tmp_path)
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
    assert '<select id="control_plane_model" name="control_plane_model"' in response.text
    assert 'list="control-plane-model-options"' not in response.text
    assert "<datalist" not in response.text
    assert "Custom model…" in response.text
    assert 'name="custom_control_plane_model"' in response.text
    assert "claude-fable-5" in response.text
    assert "claude-opus-4-8" in response.text
    assert "claude-sonnet-4-6" in response.text
    assert "claude-haiku-4-5" in response.text
    assert "anthropic/claude-sonnet-4-20250514" not in response.text
    assert 'data-provider="openai"' in _model_option(response.text, "gpt-5.4-mini")
    _assert_selectable(_model_option(response.text, "gpt-5.4-mini"))
    _assert_selectable(_model_option(response.text, "gpt-5.5"))
    _assert_not_selectable(_model_option(response.text, "claude-fable-5"))
    _assert_not_selectable(_model_option(response.text, "claude-opus-4-8"))
    _assert_not_selectable(_model_option(response.text, "claude-sonnet-4-6"))
    _assert_not_selectable(_model_option(response.text, "claude-haiku-4-5"))
    assert "Save control-plane model" in response.text
    assert 'name="control_plane_api_key" type="password"' in response.text
    assert "Leave blank to keep the existing key" in response.text
    assert "Required for OpenAI-compatible endpoints" in response.text
    assert "Advanced connection settings" in response.text
    assert "https://example.invalid/v1" not in response.text
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
    assert "claude-sonnet-4-6" in html
    assert 'data-provider="anthropic"' in _model_option(html, "claude-sonnet-4-6")
    _assert_selectable(_model_option(html, "claude-fable-5"))
    _assert_selectable(_model_option(html, "claude-opus-4-8"))
    _assert_selectable(_model_option(html, "claude-sonnet-4-6"))
    _assert_selectable(_model_option(html, "claude-haiku-4-5"))
    _assert_not_selectable(_model_option(html, "gpt-5.4-mini"))
    _assert_not_selectable(_model_option(html, "gpt-5.5"))
    assert "TEST_CONTROL_PLANE_KEY" in html
    assert "AGILE-AI-HTB orchestration model" in html
    assert "Worker Harness" in html
    assert "sk_sho...nder" not in html

def test_control_plane_settings_page_preserves_existing_custom_model(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    custom_model = "acme/custom-control-plane-999"
    with _client_with_control_plane_llm(tmp_path, FakeControlPlaneLLM(), control_plane_model=custom_model) as client:
        response = client.get("/settings/control-plane", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert '<option value="__custom__" selected>Custom model…</option>' in html
    assert f'name="custom_control_plane_model" value="{custom_model}"' in html

def test_control_plane_settings_page_preserves_openai_compatible_model_as_custom(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    custom_model = "openai-compatible/custom-control-plane-999"
    with _client_with_control_plane_llm(
        tmp_path,
        FakeControlPlaneLLM(),
        control_plane_provider="openai-compatible",
        control_plane_model=custom_model,
        control_plane_base_url="https://example.invalid/v1",
    ) as client:
        response = client.get("/settings/control-plane", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert '<option value="openai-compatible" selected>openai-compatible</option>' in html
    assert '<option value="__custom__" selected>Custom model…</option>' in html
    assert f'name="custom_control_plane_model" value="{custom_model}"' in html
    _assert_not_selectable(_model_option(html, "gpt-5.4-mini"))
    _assert_not_selectable(_model_option(html, "gpt-5.5"))
    _assert_not_selectable(_model_option(html, "claude-sonnet-4-6"))


def test_control_plane_settings_page_preserves_provider_incompatible_model_as_custom(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    mismatched_model = "claude-sonnet-4-6"
    with _client_with_control_plane_llm(
        tmp_path,
        FakeControlPlaneLLM(),
        control_plane_provider="openai",
        control_plane_model=mismatched_model,
    ) as client:
        response = client.get("/settings/control-plane", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert '<option value="openai" selected>openai</option>' in html
    assert '<option value="__custom__" selected>Custom model…</option>' in html
    assert f'name="custom_control_plane_model" value="{mismatched_model}"' in html
    _assert_selectable(_model_option(html, "gpt-5.4-mini"))
    _assert_not_selectable(_model_option(html, mismatched_model))


def test_control_plane_settings_page_preserves_stale_provider_prefixed_model_as_custom(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    stale_model = "anthropic/claude-sonnet-4-20250514"
    with _client_with_control_plane_llm(tmp_path, FakeControlPlaneLLM(), control_plane_model=stale_model) as client:
        response = client.get("/settings/control-plane", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert '<option value="__custom__" selected>Custom model…</option>' in html
    assert f'name="custom_control_plane_model" value="{stale_model}"' in html

def test_control_plane_form_custom_model_submission_uses_custom_value(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    custom_model = "acme/custom-control-plane-999"

    with _client(tmp_path) as client:
        response = client.post(
            "/settings/control-plane",
            headers=_portal_headers(),
            data={
                "control_plane_provider": "openai-compatible",
                "control_plane_model": "__custom__",
                "custom_control_plane_model": custom_model,
                "control_plane_base_url": "https://example.invalid/v1",
                "control_plane_api_key_env": "COMPATIBLE_API_KEY",
                "apply_to_estimator_breakdown": "on",
            },
        )

    assert response.status_code == 200
    assert custom_model in response.text
    config = load_operator_config(tmp_path / ".htb" / "config.toml")
    assert config["control_plane_provider"] == "openai-compatible"
    assert config["control_plane_model"] == custom_model
    assert config["estimator_model"] == custom_model
    assert config["task_breakdown_model"] == custom_model

def test_control_plane_connection_test_records_sanitized_status(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeControlPlaneLLM()
    with _client_with_control_plane_llm(tmp_path, llm) as client:
        response = client.post("/settings/control-plane/test", headers=_portal_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["status"]["online"] is True
    assert body["status"]["details"]["model"] == "claude-sonnet-4-6"
    assert body["status"]["details"]["usage"]["total_tokens"] == 10
    assert "«redacted:sk_…»" not in str(body)
    assert llm.requests[0]["model"] == "claude-sonnet-4-6"


def test_control_plane_connection_test_browser_success_returns_to_settings_ui(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeControlPlaneLLM()
    headers = {**_portal_headers(), "accept": "text/html"}
    with _client_with_control_plane_llm(tmp_path, llm) as client:
        response = client.post("/settings/control-plane/test", headers=headers, follow_redirects=False)
        page = client.get("/settings/control-plane", headers=headers)

    assert response.status_code == 303
    assert response.headers["location"] == "/settings/control-plane"
    assert "online" in page.text
    assert "Total tokens</div><div class=\"v\">10" in page.text
    assert "Raw sanitized details" in page.text
    assert "sk_sho...nder" not in page.text

def test_control_plane_connection_test_does_not_cap_gpt5_smoke_response(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeControlPlaneLLM()
    with _client_with_control_plane_llm(
        tmp_path,
        llm,
        control_plane_provider="openai",
        control_plane_model="gpt-5.4-mini",
    ) as client:
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


def test_control_plane_connection_test_browser_failure_returns_to_settings_ui(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeControlPlaneLLM(exc=RuntimeError("secret sk_bad_key"))
    headers = {**_portal_headers(), "accept": "text/html"}
    with _client_with_control_plane_llm(tmp_path, llm) as client:
        response = client.post("/settings/control-plane/test", headers=headers, follow_redirects=False)
        page = client.get("/settings/control-plane", headers=headers)

    assert response.status_code == 303
    assert response.headers["location"] == "/settings/control-plane"
    assert "offline" in page.text
    assert "RuntimeError" in page.text
    assert "***REDACTED***" in page.text
    assert "sk_bad_key" not in page.text

