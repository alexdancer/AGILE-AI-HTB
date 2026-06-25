from agile_ai_htb.operator_config import (
    CONTROL_API_KEY_PLACEHOLDER,
    ensure_secret_placeholder,
    load_operator_config,
    update_operator_config,
)


def test_update_operator_config_preserves_unrelated_values(tmp_path):
    config_path = tmp_path / ".htb" / "config.toml"
    config_path.parent.mkdir()
    config_path.write_text(
        'database_path = "custom.db"\n'
        'control_plane_model = "old-model"\n'
        'local_runner_enabled = true\n',
        encoding="utf-8",
    )

    config = update_operator_config(
        config_path,
        control_plane_provider="anthropic",
        control_plane_model="claude-haiku-4-5",
        control_plane_api_key_env="ANTHROPIC_API_KEY",
    )

    assert config["database_path"] == "custom.db"
    assert config["local_runner_enabled"] is True
    assert config["control_plane_provider"] == "anthropic"
    assert config["control_plane_model"] == "claude-haiku-4-5"
    assert load_operator_config(config_path)["control_plane_api_key_env"] == "ANTHROPIC_API_KEY"


def test_ensure_secret_placeholder_adds_missing_env_without_overwriting(tmp_path):
    secrets_path = tmp_path / ".htb" / "secrets.env"
    secrets_path.parent.mkdir()
    secrets_path.write_text("EXISTING_KEY='real-value'\n", encoding="utf-8")

    values = ensure_secret_placeholder("NEW_CONTROL_KEY", secrets_path)

    assert values["EXISTING_KEY"] == "real-value"
    assert values["NEW_CONTROL_KEY"] == CONTROL_API_KEY_PLACEHOLDER
    text = secrets_path.read_text(encoding="utf-8")
    assert "EXISTING_KEY=real-value" in text or "EXISTING_KEY='real-value'" in text
    assert f"NEW_CONTROL_KEY='{CONTROL_API_KEY_PLACEHOLDER}'" in text


def test_ensure_secret_placeholder_preserves_existing_secret(tmp_path):
    secrets_path = tmp_path / ".htb" / "secrets.env"
    secrets_path.parent.mkdir()
    secrets_path.write_text("CONTROL_KEY='keep-me'\n", encoding="utf-8")

    values = ensure_secret_placeholder("CONTROL_KEY", secrets_path)

    assert values["CONTROL_KEY"] == "keep-me"
    assert "keep-me" in secrets_path.read_text(encoding="utf-8")
