from pathlib import Path

from agile_ai_htb import db
from agile_ai_htb.cli import main


ROOT = Path(__file__).resolve().parents[1]


def _clear_cli_env(monkeypatch):
    for name in [
        "TOKEN_TRACKER_DATABASE_PATH",
        "TOKEN_TRACKER_GUARDRAILS_PATH",
        "AGILE_AI_HTB_CONTROL_MODEL",
        "AGILE_AI_HTB_CONTROL_API_KEY",
        "AGILE_AI_HTB_CONTROL_API_KEY_ENV",
        "TOKEN_TRACKER_CONTROL_PLANE_MODEL",
        "TOKEN_TRACKER_CONTROL_PLANE_API_KEY_ENV",
        "TOKEN_TRACKER_LOCAL_RUNNER",
        "TOKEN_TRACKER_PORTAL_TOKEN",
        "TOKEN_TRACKER_PORTAL_TOKEN_ENV",
    ]:
        monkeypatch.delenv(name, raising=False)


def test_bare_htb_defaults_to_serve(monkeypatch, tmp_path):
    calls = []
    _clear_cli_env(monkeypatch)

    def fake_run(app_ref, **kwargs):
        calls.append((app_ref, kwargs))

    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", fake_run)

    exit_code = main([
        "--database-path",
        str(tmp_path / "harness.db"),
        "--guardrails-path",
        str(ROOT / "guardrails.yaml"),
    ])

    assert exit_code == 0
    assert calls == [
        (
            "agile_ai_htb.app:create_app",
            {
                "host": "127.0.0.1",
                "port": 8000,
                "proxy_headers": False,
                "factory": True,
                "env_file": None,
            },
        )
    ]


def test_serve_cli_arguments_override_environment(monkeypatch, tmp_path):
    calls = []
    _clear_cli_env(monkeypatch)
    monkeypatch.setenv("TOKEN_TRACKER_DATABASE_PATH", "env-harness.db")
    monkeypatch.setenv("TOKEN_TRACKER_GUARDRAILS_PATH", "env-guardrails.yaml")
    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", lambda app_ref, **kwargs: calls.append((app_ref, kwargs)))

    exit_code = main([
        "serve",
        "--host",
        "0.0.0.0",
        "--port",
        "9009",
        "--database-path",
        str(tmp_path / "cli-harness.db"),
        "--guardrails-path",
        str(ROOT / "guardrails.yaml"),
    ])

    assert exit_code == 0
    assert calls[0][1]["host"] == "0.0.0.0"
    assert calls[0][1]["port"] == 9009
    assert calls[0][1]["factory"] is True
    assert calls[0][1]["env_file"] is None


def test_serve_local_runner_flag_sets_backend_environment(monkeypatch, tmp_path):
    calls = []
    _clear_cli_env(monkeypatch)
    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", lambda app_ref, **kwargs: calls.append((app_ref, kwargs)))

    exit_code = main([
        "serve",
        "--database-path",
        str(tmp_path / "cli-harness.db"),
        "--guardrails-path",
        str(ROOT / "guardrails.yaml"),
        "--local-runner",
    ])

    assert exit_code == 0
    assert calls[0][0] == "agile_ai_htb.app:create_app"
    assert calls[0][1]["factory"] is True
    assert __import__("os").environ["TOKEN_TRACKER_LOCAL_RUNNER"] == "1"


def test_init_writes_non_secret_operator_config(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)

    exit_code = main(["init"])

    assert exit_code == 0
    config = tmp_path / ".htb" / "config.toml"
    secrets = tmp_path / ".htb" / "secrets.env"
    content = config.read_text()
    secret_content = secrets.read_text()
    assert "control_plane_model = \"gpt-5.4-mini\"" in content
    assert "local_runner_enabled = true" in content
    assert "env var NAMES, not secret values" in content
    assert "your-control-plane-api-key" not in content
    assert "TOKEN_TRACKER_PORTAL_TOKEN=htb-" in secret_content
    assert "AGILE_AI_HTB_CONTROL_API_KEY='<your-control-plane-api-key>'" in secret_content
    output = capsys.readouterr().out
    assert "Wrote .htb/config.toml" in output
    assert "Wrote .htb/secrets.env" in output
    assert "Edit .htb/secrets.env once" in output
    assert "Portal login token: set TOKEN_TRACKER_PORTAL_TOKEN" in output
    assert "Control-plane API key: replace AGILE_AI_HTB_CONTROL_API_KEY=<your-control-plane-api-key>" in output
    assert "export TOKEN_TRACKER_PORTAL_TOKEN" not in output


def test_init_preserves_existing_config_and_prints_configured_secret_env_names(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    capsys.readouterr()
    config = tmp_path / ".htb" / "config.toml"
    content = config.read_text()
    content = content.replace('portal_token_env = "TOKEN_TRACKER_PORTAL_TOKEN"', 'portal_token_env = "CUSTOM_PORTAL_TOKEN"')
    content = content.replace(
        'control_plane_api_key_env = "AGILE_AI_HTB_CONTROL_API_KEY"',
        'control_plane_api_key_env = "CUSTOM_CONTROL_API_KEY"',
    )
    content = content.replace('control_plane_model = "gpt-5.4-mini"', 'control_plane_model = "custom-model"')
    config.write_text(content)

    exit_code = main(["init"])

    assert exit_code == 0
    rewritten = config.read_text()
    secrets = tmp_path / ".htb" / "secrets.env"
    secret_content = secrets.read_text()
    assert 'portal_token_env = "CUSTOM_PORTAL_TOKEN"' in rewritten
    assert 'control_plane_api_key_env = "CUSTOM_CONTROL_API_KEY"' in rewritten
    assert 'control_plane_model = "custom-model"' in rewritten
    assert "CUSTOM_PORTAL_TOKEN=htb-" in secret_content
    assert "CUSTOM_CONTROL_API_KEY='<your-control-plane-api-key>'" in secret_content
    output = capsys.readouterr().out
    assert "Edit .htb/secrets.env once" in output
    assert "Portal login token: set CUSTOM_PORTAL_TOKEN" in output
    assert "Control-plane API key: replace CUSTOM_CONTROL_API_KEY=<your-control-plane-api-key>" in output


def test_init_migrates_secret_values_mistakenly_written_as_env_names(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    capsys.readouterr()
    config = tmp_path / ".htb" / "config.toml"
    config.write_text(
        config.read_text()
        .replace('portal_token_env = "TOKEN_TRACKER_PORTAL_TOKEN"', 'portal_token_env = "demo-token"')
        .replace(
            'control_plane_api_key_env = "AGILE_AI_HTB_CONTROL_API_KEY"',
            'control_plane_api_key_env = "sk-proj-secret"',
        )
    )

    exit_code = main(["init"])

    assert exit_code == 0
    rewritten = config.read_text()
    assert 'portal_token_env = "TOKEN_TRACKER_PORTAL_TOKEN"' in rewritten
    assert 'control_plane_api_key_env = "AGILE_AI_HTB_CONTROL_API_KEY"' in rewritten
    secret_content = (tmp_path / ".htb" / "secrets.env").read_text()
    assert "TOKEN_TRACKER_PORTAL_TOKEN=htb-" in secret_content
    assert "AGILE_AI_HTB_CONTROL_API_KEY='<your-control-plane-api-key>'" in secret_content


def test_serve_reads_operator_config_when_flags_missing(monkeypatch, tmp_path):
    calls = []
    monkeypatch.chdir(tmp_path)
    _clear_cli_env(monkeypatch)
    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", lambda app_ref, **kwargs: calls.append((app_ref, kwargs)))
    assert main(["init"]) == 0
    secrets = tmp_path / ".htb" / "secrets.env"
    secrets.write_text(
        secrets.read_text().replace(
            "AGILE_AI_HTB_CONTROL_API_KEY='<your-control-plane-api-key>'",
            "AGILE_AI_HTB_CONTROL_API_KEY='sk-test-control-key'",
        )
    )

    exit_code = main(["serve"])

    assert exit_code == 0
    assert calls[0][1]["host"] == "127.0.0.1"
    assert calls[0][1]["port"] == 8000
    assert __import__("os").environ["TOKEN_TRACKER_DATABASE_PATH"] == ".htb/harness.db"
    assert __import__("os").environ["AGILE_AI_HTB_CONTROL_MODEL"] == "gpt-5.4-mini"
    assert __import__("os").environ["TOKEN_TRACKER_PORTAL_TOKEN"].startswith("htb-")
    assert __import__("os").environ["AGILE_AI_HTB_CONTROL_API_KEY"] == "sk-test-control-key"
    assert __import__("os").environ["TOKEN_TRACKER_LOCAL_RUNNER"] == "1"


def test_serve_preserves_legacy_env_alias_over_config(monkeypatch, tmp_path):
    calls = []
    monkeypatch.chdir(tmp_path)
    _clear_cli_env(monkeypatch)
    monkeypatch.setenv("TOKEN_TRACKER_CONTROL_PLANE_MODEL", "legacy-env-model")
    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", lambda app_ref, **kwargs: calls.append((app_ref, kwargs)))
    assert main(["init"]) == 0
    config = tmp_path / ".htb" / "config.toml"
    config.write_text(config.read_text().replace('control_plane_model = "gpt-5.4-mini"', 'control_plane_model = "config-model"'))

    exit_code = main(["serve"])

    assert exit_code == 0
    assert calls
    assert "AGILE_AI_HTB_CONTROL_MODEL" not in __import__("os").environ
    assert __import__("os").environ["TOKEN_TRACKER_CONTROL_PLANE_MODEL"] == "legacy-env-model"


def test_serve_preserves_local_runner_env_override_over_config(monkeypatch, tmp_path):
    calls = []
    monkeypatch.chdir(tmp_path)
    _clear_cli_env(monkeypatch)
    monkeypatch.setenv("TOKEN_TRACKER_LOCAL_RUNNER", "0")
    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", lambda app_ref, **kwargs: calls.append((app_ref, kwargs)))
    assert main(["init"]) == 0

    exit_code = main(["serve"])

    assert exit_code == 0
    assert calls
    assert __import__("os").environ["TOKEN_TRACKER_LOCAL_RUNNER"] == "0"


def test_check_reports_missing_required_env_without_secret_values(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    capsys.readouterr()
    monkeypatch.delenv("TOKEN_TRACKER_PORTAL_TOKEN_ENV", raising=False)
    monkeypatch.delenv("AGILE_AI_HTB_CONTROL_API_KEY_ENV", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_PORTAL_TOKEN", raising=False)
    monkeypatch.delenv("AGILE_AI_HTB_CONTROL_API_KEY", raising=False)

    exit_code = main(["check"])

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "PASS portal token env TOKEN_TRACKER_PORTAL_TOKEN present" in output
    assert "FAIL control-plane API key env AGILE_AI_HTB_CONTROL_API_KEY missing" in output
    assert "sk-" not in output


def test_check_reports_control_plane_and_observed_only_worker(monkeypatch, tmp_path, capsys):
    class FakeLLMClient:
        def __init__(self, settings):
            self.settings = settings

        async def acompletion(self, payload):
            return {"usage": {"total_tokens": 1}}

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TOKEN_TRACKER_DATABASE_PATH", raising=False)
    monkeypatch.delenv("AGILE_AI_HTB_CONTROL_MODEL", raising=False)
    monkeypatch.delenv("TOKEN_TRACKER_PORTAL_TOKEN_ENV", raising=False)
    monkeypatch.delenv("AGILE_AI_HTB_CONTROL_API_KEY_ENV", raising=False)
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", "portal-secret")
    monkeypatch.setenv("AGILE_AI_HTB_CONTROL_API_KEY", "control-secret")
    monkeypatch.setattr("agile_ai_htb.cli.LLMClient", FakeLLMClient)
    assert main(["init"]) == 0
    db_path = tmp_path / ".htb" / "harness.db"
    db.init_db(db_path)
    workdir = tmp_path / "worker"
    workdir.mkdir()
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(workdir),
        config={"native_launch_template": ["opencode", "run"]},
        supported_models=["openai/gpt-5.5"],
    )
    db.mark_worker_adapter_verification(
        db_path,
        "opencode",
        verified=True,
        evidence={"tracking_mode": "observed_only", "tracking_authoritative": False},
    )
    capsys.readouterr()

    exit_code = main(["check"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "PASS control-plane model gpt-5.4-mini reachable" in output
    assert "WARN Worker adapter opencode (opencode) observed_only is diagnostic-only" in output


def test_seed_demo_inserts_synthetic_tasks(tmp_path, capsys):
    db_path = tmp_path / "harness.db"

    exit_code = main(["--database-path", str(db_path), "seed-demo"])

    assert exit_code == 0
    tasks = {task["id"]: task for task in db.list_tasks(db_path)}
    assert "DEMO_TASK_2099_T1" in tasks
    assert "DEMO_TASK_2099_T6" in tasks
    assert "inserted 6" in capsys.readouterr().out


def test_seed_demo_is_idempotent(tmp_path, capsys):
    db_path = tmp_path / "harness.db"

    assert main(["--database-path", str(db_path), "seed-demo"]) == 0
    assert main(["--database-path", str(db_path), "seed-demo"]) == 0

    assert len(db.list_tasks(db_path)) == 6
    assert "inserted 0" in capsys.readouterr().out
