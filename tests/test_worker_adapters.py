import os
import subprocess
from pathlib import Path

from agile_ai_htb import db
from agile_ai_htb.worker_adapters import CommandPlan, get_adapter_builder, redact_command_plan, subprocess_runner


def test_init_db_seeds_worker_adapter_presets_idempotently_and_preserves_updates(tmp_path):
    db_path = tmp_path / "harness.db"

    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "codex",
        workdir=str(tmp_path),
        config={"command": "codex", "env": {"OPENAI_API_KEY": "secret-value"}},
        supported_models=["gpt-5.1-codex"],
        is_default=True,
    )
    db.init_db(db_path)

    adapters = db.list_worker_adapters(db_path)
    by_id = {adapter["id"]: adapter for adapter in adapters}
    assert {"claude_code", "codex", "opencode"}.issubset(by_id)
    assert by_id["codex"]["workdir"] == str(tmp_path)
    assert by_id["codex"]["supported_models"] == ["gpt-5.1-codex"]
    assert by_id["codex"]["is_default"] is True
    assert sum(1 for adapter in adapters if adapter["is_default"]) == 1
    assert by_id["codex"]["config"]["env"]["OPENAI_API_KEY"] == "secret-value"


def test_worker_adapter_status_helpers_store_sanitized_evidence(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)

    db.mark_worker_adapter_verification(
        db_path,
        "claude_code",
        verified=True,
        evidence={
            "stdout": "AGILE_AI_HTB_ADAPTER_OK",
            "env": {"AGILE_AI_HTB_SESSION_API_KEY": "sk_sess_secret", "SAFE_FLAG": "ok"},
            "command": ["claude", "--api-key", "secret"],
        },
    )

    adapter = db.get_worker_adapter(db_path, "claude_code")
    evidence = adapter["verification_evidence"]
    assert adapter["verification_status"] == "verified"
    assert adapter["verified_at"]
    serialized = str(evidence)
    assert "secret" not in serialized
    assert "sk_sess_" not in serialized
    assert "***REDACTED***" in serialized



def test_worker_adapter_builders_create_safe_configurable_command_plans(tmp_path):
    adapter = {
        "id": "codex",
        "kind": "codex",
        "name": "Codex CLI",
        "workdir": str(tmp_path),
        "config": {"verification_template": ["codex", "--model", "{model}", "--prompt", "{prompt}"]},
        "supported_models": ["gpt-5.1-codex"],
    }
    builder = get_adapter_builder(adapter)

    session_api_key = "test-session-key"
    plan = builder.build_verification_command(
        model="gpt-5.1-codex",
        prompt="Return sentinel",
        proxy_url="http://127.0.0.1:8000/v1",
        session_api_key=session_api_key,
    )
    safe = redact_command_plan(plan)

    assert builder.supports_model("gpt-5.1-codex") is True
    assert builder.supports_model("claude-3-haiku") is False
    assert plan.command == ["codex", "--model", "gpt-5.1-codex", "--prompt", "Return sentinel"]
    assert plan.cwd == Path(tmp_path)
    assert plan.env["OPENAI_BASE_URL"] == "http://127.0.0.1:8000/v1"
    assert plan.env["OPENAI_API_KEY"] == session_api_key
    assert session_api_key not in str(safe)
    assert safe["env"]["OPENAI_API_KEY"] == "***REDACTED***"


def test_redact_command_plan_redacts_secret_flag_values_without_over_redacting(tmp_path):
    safe = redact_command_plan(
        CommandPlan(
            command=[
                "tool",
                "--api-key",
                "abc123",
                "--model",
                "gpt-5.1-codex",
                "--token=tok456",
                "-H",
                "Authorization: Basic abc123",
                "--prompt",
                "secret words are already redacted by value scanner",
            ],
            cwd=tmp_path,
            env={},
            metadata={},
        )
    )

    assert safe["command"] == [
        "tool",
        "--api-key",
        "***REDACTED***",
        "--model",
        "gpt-5.1-codex",
        "--token=***REDACTED***",
        "-H",
        "***REDACTED***",
        "--prompt",
        "***REDACTED***",
    ]


def test_subprocess_runner_inherits_environment_and_applies_overrides_and_timeout(monkeypatch, tmp_path):
    monkeypatch.setenv("AGILE_AI_HTB_INHERITED", "from-parent")
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = subprocess_runner(
        CommandPlan(
            command=["worker", "verify"],
            cwd=tmp_path,
            env={"AGILE_AI_HTB_OVERRIDE": "from-plan", "AGILE_AI_HTB_INHERITED": "overridden"},
            metadata={},
        )
    )

    assert result.returncode == 0
    assert calls[0][1]["env"]["AGILE_AI_HTB_OVERRIDE"] == "from-plan"
    assert calls[0][1]["env"]["AGILE_AI_HTB_INHERITED"] == "overridden"
    assert os.environ["PATH"] == calls[0][1]["env"]["PATH"]
    assert calls[0][1]["timeout"] > 0


def test_subprocess_runner_returns_failed_result_on_timeout(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"], output="partial", stderr="late")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = subprocess_runner(CommandPlan(command=["slow-worker"], cwd=None, env={}, metadata={}))

    assert result.returncode != 0
    assert result.stdout == "partial"
    assert "timed out" in result.stderr


def test_subprocess_runner_returns_failed_result_when_cli_cannot_launch(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", args[0][0])

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = subprocess_runner(
        CommandPlan(command=["missing-worker", "--api-key", "abc123"], cwd=None, env={}, metadata={})
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert "Failed to launch command" in result.stderr
    assert "missing-worker" in result.stderr
    assert "abc123" not in result.stderr
