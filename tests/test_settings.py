from pathlib import Path


def test_settings_defaults_point_to_local_development_files(monkeypatch):
    monkeypatch.delenv("TOKEN_TRACKER_DATABASE_PATH", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_GUARDRAILS_PATH", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_TIMEZONE", raising=False)
    monkeypatch.delenv("AGILE_AI_HTB_CONTROL_PROVIDER", raising=False)
    monkeypatch.delenv("AGILE_AI_HTB_CONTROL_MODEL", raising=False)
    monkeypatch.delenv("AGILE_AI_HTB_CONTROL_API_KEY_ENV", raising=False)
    monkeypatch.delenv("AGILE_AI_HTB_CONTROL_BASE_URL", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_PROVIDER_API_KEY_ENV", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_ESTIMATOR_MODEL", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_PORTAL_TOKEN_ENV", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_PORTAL_COOKIE_SECURE", raising=False)

    from agile_ai_htb.settings import Settings

    settings = Settings()

    assert settings.database_path == Path("harness.db")
    assert settings.guardrails_path == Path("guardrails.yaml")
    assert settings.timezone == "local"
    assert settings.control_plane_provider == "openai"
    assert settings.control_plane_model == "gpt-4o-mini"
    assert settings.control_plane_api_key_env == "AGILE_AI_HTB_CONTROL_API_KEY"
    assert settings.control_plane_base_url == ""
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
    monkeypatch.setenv("AGILE_AI_HTB_CONTROL_PROVIDER", "anthropic")
    monkeypatch.setenv("AGILE_AI_HTB_CONTROL_MODEL", "anthropic/claude-sonnet-4-20250514")
    monkeypatch.setenv("AGILE_AI_HTB_CONTROL_API_KEY_ENV", "CUSTOM_CONTROL_KEY")
    monkeypatch.setenv("AGILE_AI_HTB_CONTROL_BASE_URL", "https://provider.example/v1")
    monkeypatch.setenv("TOKEN_TRACKER_PROVIDER_API_KEY_ENV", "ANTHROPIC_API_KEY")
    monkeypatch.setenv("TOKEN_TRACKER_ESTIMATOR_MODEL", "openai/gpt-4.1-mini")
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN_ENV", "CUSTOM_PORTAL_TOKEN")
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_COOKIE_SECURE", "true")

    from agile_ai_htb.settings import Settings

    settings = Settings()

    assert settings.database_path == database_path
    assert settings.guardrails_path == guardrails_path
    assert settings.timezone == "America/Chicago"
    assert settings.control_plane_provider == "anthropic"
    assert settings.control_plane_model == "anthropic/claude-sonnet-4-20250514"
    assert settings.control_plane_api_key_env == "CUSTOM_CONTROL_KEY"
    assert settings.control_plane_base_url == "https://provider.example/v1"
    assert settings.provider_api_key_env == "ANTHROPIC_API_KEY"
    assert settings.estimator_model == "anthropic/claude-sonnet-4-20250514"
    assert settings.portal_token_env == "CUSTOM_PORTAL_TOKEN"
    assert settings.portal_cookie_secure is True


def test_settings_keeps_legacy_estimator_model_as_control_plane_alias(monkeypatch):
    monkeypatch.delenv("AGILE_AI_HTB_CONTROL_MODEL", raising=False)
    monkeypatch.setenv("TOKEN_TRACKER_ESTIMATOR_MODEL", "openai/gpt-4.1-mini")

    from agile_ai_htb.settings import Settings

    settings = Settings()

    assert settings.control_plane_model == "openai/gpt-4.1-mini"
    assert settings.estimator_model == "openai/gpt-4.1-mini"
