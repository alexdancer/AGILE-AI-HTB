from pathlib import Path


def test_settings_defaults_point_to_local_development_files(monkeypatch):
    monkeypatch.delenv("TOKEN_TRACKER_DATABASE_PATH", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_GUARDRAILS_PATH", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_TIMEZONE", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_PROVIDER_API_KEY_ENV", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_ESTIMATOR_MODEL", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_PORTAL_TOKEN_ENV", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_PORTAL_COOKIE_SECURE", raising=False)

    from agile_ai_htb.settings import Settings

    settings = Settings()

    assert settings.database_path == Path("harness.db")
    assert settings.guardrails_path == Path("guardrails.yaml")
    assert settings.timezone == "local"
    assert settings.provider_api_key_env == "PROVIDER_API_KEY"
    assert settings.estimator_model == "gpt-4o-mini"
    assert settings.portal_token_env == "TOKEN_TRACKER_PORTAL_TOKEN"
    assert settings.portal_cookie_secure is False


def test_settings_reads_environment_overrides(monkeypatch, tmp_path):
    database_path = tmp_path / "custom-harness.db"
    guardrails_path = tmp_path / "custom-guardrails.yaml"
    monkeypatch.setenv("TOKEN_TRACKER_DATABASE_PATH", str(database_path))
    monkeypatch.setenv("TOKEN_TRACKER_GUARDRAILS_PATH", str(guardrails_path))
    monkeypatch.setenv("TOKEN_TRACKER_TIMEZONE", "America/Chicago")
    monkeypatch.setenv("TOKEN_TRACKER_PROVIDER_API_KEY_ENV", "ANTHROPIC_API_KEY")
    monkeypatch.setenv("TOKEN_TRACKER_ESTIMATOR_MODEL", "openai/gpt-4.1-mini")
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN_ENV", "CUSTOM_PORTAL_TOKEN")
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_COOKIE_SECURE", "true")

    from agile_ai_htb.settings import Settings

    settings = Settings()

    assert settings.database_path == database_path
    assert settings.guardrails_path == guardrails_path
    assert settings.timezone == "America/Chicago"
    assert settings.provider_api_key_env == "ANTHROPIC_API_KEY"
    assert settings.estimator_model == "openai/gpt-4.1-mini"
    assert settings.portal_token_env == "CUSTOM_PORTAL_TOKEN"
    assert settings.portal_cookie_secure is True
