import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.cli import main


ROOT = Path(__file__).resolve().parents[2]


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
        "TOKEN_TRACKER_PORTAL_AUTH_REQUIRED",
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
    assert __import__("os").environ["TOKEN_TRACKER_PORTAL_AUTH_REQUIRED"] == "0"


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
    assert __import__("os").environ["TOKEN_TRACKER_PORTAL_AUTH_REQUIRED"] == "1"


def test_serve_proxy_headers_keep_portal_auth_required_on_loopback(monkeypatch, tmp_path):
    calls = []
    _clear_cli_env(monkeypatch)
    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", lambda app_ref, **kwargs: calls.append((app_ref, kwargs)))

    exit_code = main([
        "serve",
        "--proxy-headers",
        "--database-path",
        str(tmp_path / "cli-harness.db"),
        "--guardrails-path",
        str(ROOT / "guardrails.yaml"),
    ])

    assert exit_code == 0
    assert calls[0][1]["host"] == "127.0.0.1"
    assert calls[0][1]["proxy_headers"] is True
    assert __import__("os").environ["TOKEN_TRACKER_PORTAL_AUTH_REQUIRED"] == "1"


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
    assert "control_plane_model = \"gpt-5.4\"" in content
    assert "local_runner_enabled = true" in content
    assert "env var NAMES, not secret values" in content
    assert "your-control-plane-api-key" not in content
    assert "TOKEN_TRACKER_PORTAL_TOKEN=htb-" in secret_content
    assert "AGILE_AI_HTB_CONTROL_API_KEY='<your-control-plane-api-key>'" in secret_content
    output = capsys.readouterr().out
    assert "Wrote .htb/config.toml" in output
    assert "Wrote .htb/secrets.env" in output
    assert "Start with htb serve" in output
    assert "/settings/control-plane" in output
    assert "open http://localhost:8000/" in output
    assert "Portal token for shared access: set TOKEN_TRACKER_PORTAL_TOKEN" in output
    assert "Control-plane API key: configure AGILE_AI_HTB_CONTROL_API_KEY" in output
    assert ".htb/secrets.env or shell env remain supported alternatives" in output
    assert "export TOKEN_TRACKER_PORTAL_TOKEN" not in output


def test_init_creates_database_and_outside_git_ignore(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)

    assert main(["init"]) == 0
    db_path = tmp_path / ".htb" / "harness.db"
    db.create_task(db_path, description="keep this", status="Blocked")
    gitignore = tmp_path / ".htb" / ".gitignore"
    gitignore.write_text("# keep local notes\n", encoding="utf-8")
    assert main(["init"]) == 0

    assert db_path.exists()
    assert [task["description"] for task in db.list_tasks(db_path)] == ["keep this"]
    gitignore_lines = gitignore.read_text(encoding="utf-8").splitlines()
    assert "# keep local notes" in gitignore_lines
    assert "*" in gitignore_lines
    assert "!.gitignore" in gitignore_lines
    output = capsys.readouterr().out
    assert f"Initialized root {tmp_path}" in output
    assert "Wrote .htb/harness.db" in output


def test_init_from_git_subdirectory_uses_repo_root_and_exclude(monkeypatch, tmp_path, capsys):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subdir = tmp_path / "nested" / "work"
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)

    assert main(["init"]) == 0

    assert (tmp_path / ".htb" / "config.toml").exists()
    assert (tmp_path / ".htb" / "secrets.env").exists()
    assert (tmp_path / ".htb" / "guardrails.yaml").exists()
    assert (tmp_path / ".htb" / "harness.db").exists()
    assert not (subdir / ".htb").exists()
    assert ".htb/" in (tmp_path / ".git" / "info" / "exclude").read_text()
    output = capsys.readouterr().out
    assert f"Initialized root {tmp_path}" in output


def test_init_falls_back_to_cwd_when_git_is_unavailable(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    def raise_missing_git(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr("agile_ai_htb.cli.subprocess.run", raise_missing_git)

    assert main(["init"]) == 0

    assert (tmp_path / ".htb" / "config.toml").exists()
    assert (tmp_path / ".htb" / "harness.db").exists()
    assert (tmp_path / ".htb" / ".gitignore").read_text() == "*\n!.gitignore\n"


def test_init_explicit_config_and_secrets_paths_are_not_relocated(monkeypatch, tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subdir = tmp_path / "nested"
    subdir.mkdir()
    monkeypatch.chdir(subdir)

    assert main(["init", "--config-path", "local-config.toml", "--secrets-path", "local-secrets.env"]) == 0

    assert (subdir / "local-config.toml").exists()
    assert (subdir / "local-secrets.env").exists()
    assert not (tmp_path / ".htb" / "config.toml").exists()
    assert not (tmp_path / ".htb" / "secrets.env").exists()
    assert (tmp_path / ".htb" / "guardrails.yaml").exists()
    assert (tmp_path / ".htb" / "harness.db").exists()


def test_serve_from_git_subdirectory_reads_repo_root_config(monkeypatch, tmp_path):
    calls = []
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subdir = tmp_path / "nested" / "work"
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)
    _clear_cli_env(monkeypatch)
    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", lambda app_ref, **kwargs: calls.append((app_ref, kwargs)))

    assert main(["init"]) == 0
    _clear_cli_env(monkeypatch)
    assert main(["serve"]) == 0

    assert calls
    assert __import__("os").environ["TOKEN_TRACKER_DATABASE_PATH"] == str(tmp_path / ".htb" / "harness.db")
    assert __import__("os").environ["TOKEN_TRACKER_GUARDRAILS_PATH"] == str(tmp_path / ".htb" / "guardrails.yaml")
    assert __import__("os").environ["TOKEN_TRACKER_PORTAL_TOKEN"].startswith("htb-")


def test_check_from_git_subdirectory_reads_repo_root_state(monkeypatch, tmp_path, capsys):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subdir = tmp_path / "nested" / "work"
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)
    _clear_cli_env(monkeypatch)

    assert main(["init"]) == 0
    capsys.readouterr()
    _clear_cli_env(monkeypatch)

    assert main(["check"]) == 1

    output = capsys.readouterr().out
    assert f"PASS config loaded {tmp_path / '.htb' / 'config.toml'}" in output
    assert f"PASS secrets loaded {tmp_path / '.htb' / 'secrets.env'}" in output
    assert "PASS portal auth disabled for local-only access; TOKEN_TRACKER_PORTAL_TOKEN not required" in output


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
    content = content.replace('control_plane_model = "gpt-5.4"', 'control_plane_model = "custom-model"')
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
    assert "Start with htb serve" in output
    assert "/settings/control-plane" in output
    assert "Portal token for shared access: set CUSTOM_PORTAL_TOKEN" in output
    assert "Control-plane API key: configure CUSTOM_CONTROL_API_KEY" in output


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
            "AGILE_AI_HTB_CONTROL_API_KEY='fake-control-key'",
        )
    )

    exit_code = main(["serve"])

    assert exit_code == 0
    assert calls[0][1]["host"] == "127.0.0.1"
    assert calls[0][1]["port"] == 8000
    assert __import__("os").environ["TOKEN_TRACKER_DATABASE_PATH"] == str(tmp_path / ".htb" / "harness.db")
    assert __import__("os").environ["AGILE_AI_HTB_CONTROL_MODEL"] == "gpt-5.4"
    assert __import__("os").environ["TOKEN_TRACKER_PORTAL_TOKEN"].startswith("htb-")
    assert __import__("os").environ["AGILE_AI_HTB_CONTROL_API_KEY"] == "fake-control-key"
    assert __import__("os").environ["TOKEN_TRACKER_LOCAL_RUNNER"] == "1"
    assert __import__("os").environ["TOKEN_TRACKER_PORTAL_AUTH_REQUIRED"] == "0"


def test_serve_preserves_explicit_portal_auth_required_config(monkeypatch, tmp_path):
    calls = []
    monkeypatch.chdir(tmp_path)
    _clear_cli_env(monkeypatch)
    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", lambda app_ref, **kwargs: calls.append((app_ref, kwargs)))
    assert main(["init"]) == 0
    config = tmp_path / ".htb" / "config.toml"
    config.write_text(config.read_text() + "portal_auth_required = true\n")

    assert main(["serve"]) == 0

    assert calls[0][1]["host"] == "127.0.0.1"
    assert __import__("os").environ["TOKEN_TRACKER_PORTAL_AUTH_REQUIRED"] == "True"


def test_serve_preserves_legacy_env_alias_over_config(monkeypatch, tmp_path):
    calls = []
    monkeypatch.chdir(tmp_path)
    _clear_cli_env(monkeypatch)
    monkeypatch.setenv("TOKEN_TRACKER_CONTROL_PLANE_MODEL", "legacy-env-model")
    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", lambda app_ref, **kwargs: calls.append((app_ref, kwargs)))
    assert main(["init"]) == 0
    config = tmp_path / ".htb" / "config.toml"
    config.write_text(config.read_text().replace('control_plane_model = "gpt-5.4"', 'control_plane_model = "config-model"'))

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
    assert "PASS portal auth disabled for local-only access; TOKEN_TRACKER_PORTAL_TOKEN not required" in output
    assert "FAIL control-plane API key env AGILE_AI_HTB_CONTROL_API_KEY missing" in output
    assert "/settings/control-plane" in output
    assert ".htb/secrets.env" in output
    assert "shell environment" in output
    assert "does not configure native Worker CLI auth" in output
    assert "Native Worker CLI auth is separate" in output
    assert "sk-" not in output
    assert "portal-secret" not in output


def test_check_requires_portal_token_for_shared_host(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    config = tmp_path / ".htb" / "config.toml"
    config.write_text(config.read_text().replace('host = "127.0.0.1"', 'host = "0.0.0.0"'))
    secrets = tmp_path / ".htb" / "secrets.env"
    secrets.write_text(
        "\n".join(
            line for line in secrets.read_text().splitlines() if not line.startswith("TOKEN_TRACKER_PORTAL_TOKEN=")
        )
        + "\n"
    )
    capsys.readouterr()
    _clear_cli_env(monkeypatch)

    assert main(["check"]) == 1

    output = capsys.readouterr().out
    assert "FAIL portal token env TOKEN_TRACKER_PORTAL_TOKEN missing" in output
    assert "PASS portal auth disabled" not in output


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
    assert "PASS control-plane model gpt-5.4 reachable" in output
    assert "WARN Worker adapter opencode (opencode) observed_only is diagnostic-only and not normal board-launchable" in output


def test_seed_demo_inserts_synthetic_tasks(tmp_path, capsys):
    db_path = tmp_path / "harness.db"

    exit_code = main(["--database-path", str(db_path), "seed-demo"])

    assert exit_code == 0
    tasks = {task["id"]: task for task in db.list_tasks(db_path)}
    assert "DEMO_TASK_2099_T1" in tasks
    assert "DEMO_TASK_2099_T6" in tasks
    assert "inserted 6" in capsys.readouterr().out


def test_init_creates_guardrails_for_clean_cwd_app_startup(tmp_path, monkeypatch, capsys):
    _clear_cli_env(monkeypatch)
    monkeypatch.chdir(tmp_path)

    assert main(["init"]) == 0

    assert (tmp_path / ".htb" / "config.toml").exists()
    assert (tmp_path / ".htb" / "secrets.env").exists()
    assert (tmp_path / ".htb" / "guardrails.yaml").exists()
    output = capsys.readouterr().out
    assert "Wrote .htb/guardrails.yaml" in output

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200


def test_seed_demo_adapter_uses_installed_htb_command(tmp_path):
    db_path = tmp_path / "harness.db"

    assert main(["--database-path", str(db_path), "seed-demo"]) == 0

    adapter = db.get_worker_adapter(db_path, "demo_worker")
    assert adapter["config"]["command"] == "htb"
    assert adapter["config"]["verification_template"] == ["htb", "--help"]
    assert adapter["config"]["launch_template"] == ["htb", "--help"]
    assert "htb-demo-worker" not in str(adapter["config"])


def test_seed_demo_is_idempotent(tmp_path, capsys):
    db_path = tmp_path / "harness.db"

    assert main(["--database-path", str(db_path), "seed-demo"]) == 0
    assert main(["--database-path", str(db_path), "seed-demo"]) == 0

    assert len(db.list_tasks(db_path)) == 6
    assert "inserted 0" in capsys.readouterr().out
