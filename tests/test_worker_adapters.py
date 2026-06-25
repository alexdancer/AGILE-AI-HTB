import os
import subprocess
from pathlib import Path

from agile_ai_htb import db
from agile_ai_htb.worker_adapters import (
    CommandPlan,
    detect_worker_adapter,
    discover_worker_models,
    get_adapter_builder,
    redact_command_plan,
    subprocess_runner,
)


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
    assert {"claude_code", "codex", "opencode", "hermes"}.issubset(by_id)
    assert by_id["hermes"]["verification_status"] == "unverified"
    assert by_id["codex"]["workdir"] == str(tmp_path)
    assert by_id["codex"]["supported_models"] == ["gpt-5.1-codex"]
    assert by_id["codex"]["is_default"] is True
    assert sum(1 for adapter in adapters if adapter["is_default"]) == 1
    assert by_id["codex"]["config"]["env"]["OPENAI_API_KEY"] == "secret-value"
    assert by_id["opencode"]["config"]["launch_timeout_seconds"] == 600


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


def test_worker_adapter_template_can_reference_session_api_key(tmp_path):
    adapter = {
        "id": "demo_worker",
        "kind": "demo_worker",
        "name": "Demo Worker",
        "workdir": str(tmp_path),
        "config": {
            "verification_template": [
                "htb-demo-worker",
                "--prompt",
                "{prompt}",
                "--proxy-url",
                "{proxy_url}",
                "--session-key",
                "{session_api_key}",
            ]
        },
        "supported_models": ["gpt-5.4-mini"],
    }

    plan = get_adapter_builder(adapter).build_verification_command(
        model="gpt-5.4-mini",
        prompt="Return sentinel",
        proxy_url="http://127.0.0.1:8000/v1",
        session_api_key="sk_sess_test",
    )

    assert plan.command == [
        "htb-demo-worker",
        "--prompt",
        "Return sentinel",
        "--proxy-url",
        "http://127.0.0.1:8000/v1",
        "--session-key",
        "sk_sess_test",
    ]


def test_opencode_proxy_launch_template_can_reference_session_api_key(tmp_path):
    adapter = {
        "id": "opencode",
        "kind": "opencode",
        "name": "OpenCode",
        "workdir": str(tmp_path),
        "config": {"launch_template": ["opencode", "run", "--session-key", "{session_api_key}", "{prompt}"]},
        "supported_models": ["openai/gpt-5.5"],
    }

    plan = get_adapter_builder(adapter).build_launch_command(
        model="openai/gpt-5.5",
        task_prompt="Implement the task.",
        proxy_url="http://127.0.0.1:8000/v1",
        session_api_key="sk_sess_test",
        project_root=str(tmp_path),
    )

    assert "sk_sess_test" in plan.command
    assert plan.env["AGILE_AI_HTB_SESSION_API_KEY"] == "sk_sess_test"


def test_opencode_native_launch_defaults_to_agent_sized_timeout(tmp_path):
    adapter = {
        "id": "opencode",
        "kind": "opencode",
        "name": "OpenCode",
        "workdir": str(tmp_path),
        "config": {"launch_template": ["opencode"]},
        "supported_models": ["openai/gpt-5.5"],
    }

    plan = get_adapter_builder(adapter).build_native_launch_command(
        model="openai/gpt-5.5",
        task_prompt="Implement the DEMO_2099 task and run tests.",
    )

    assert plan.command == [
        "opencode",
        "run",
        "--dir",
        str(tmp_path),
        "--model",
        "openai/gpt-5.5",
        "--format",
        "json",
        "Implement the DEMO_2099 task and run tests.",
    ]
    assert plan.cwd == Path(tmp_path)
    assert plan.metadata["timeout_seconds"] == 600


def test_opencode_native_verification_includes_configured_workdir(tmp_path):
    adapter = {
        "id": "opencode",
        "kind": "opencode",
        "name": "OpenCode",
        "workdir": str(tmp_path),
        "config": {},
        "supported_models": ["openai/gpt-5.5"],
    }

    plan = get_adapter_builder(adapter).build_native_verification_command(
        model="openai/gpt-5.5",
        prompt="Return AGILE_AI_HTB_ADAPTER_OK",
    )

    assert plan.command == [
        "opencode",
        "run",
        "--dir",
        str(tmp_path),
        "--model",
        "openai/gpt-5.5",
        "--format",
        "json",
        "Return AGILE_AI_HTB_ADAPTER_OK",
    ]
    assert plan.cwd == Path(tmp_path)


def test_opencode_native_launch_template_with_dir_is_not_duplicated(tmp_path):
    adapter = {
        "id": "opencode",
        "kind": "opencode",
        "name": "OpenCode",
        "workdir": str(tmp_path),
        "config": {
            "native_launch_template": [
                "opencode",
                "run",
                "--dir",
                "{workdir}",
                "--model",
                "{model}",
                "--format",
                "json",
                "{prompt}",
            ]
        },
        "supported_models": ["openai/gpt-5.5"],
    }

    plan = get_adapter_builder(adapter).build_native_launch_command(
        model="openai/gpt-5.5",
        task_prompt="Implement the task.",
    )

    assert plan.command.count("--dir") == 1
    assert plan.command == [
        "opencode",
        "run",
        "--dir",
        str(tmp_path),
        "--model",
        "openai/gpt-5.5",
        "--format",
        "json",
        "Implement the task.",
    ]


def test_opencode_native_launch_template_without_dir_is_injected(tmp_path):
    adapter = {
        "id": "opencode",
        "kind": "opencode",
        "name": "OpenCode",
        "workdir": str(tmp_path),
        "config": {
            "native_launch_template": ["opencode", "run", "--model", "{model}", "--format", "json", "{prompt}"]
        },
        "supported_models": ["openai/gpt-5.5"],
    }

    plan = get_adapter_builder(adapter).build_native_launch_command(
        model="openai/gpt-5.5",
        task_prompt="Implement the task.",
    )

    assert plan.command[:4] == ["opencode", "run", "--dir", str(tmp_path)]


def test_opencode_launch_template_with_stale_dir_uses_project_root(tmp_path):
    stale_root = tmp_path / "stale"
    project_root = tmp_path / "project"
    adapter = {
        "id": "opencode",
        "kind": "opencode",
        "name": "OpenCode",
        "workdir": str(stale_root),
        "config": {
            "launch_template": ["opencode", "run", "--dir", str(stale_root), "--model", "{model}", "{prompt}"]
        },
        "supported_models": ["openai/gpt-5.5"],
    }

    plan = get_adapter_builder(adapter).build_launch_command(
        model="openai/gpt-5.5",
        task_prompt="Implement the task.",
        proxy_url="http://127.0.0.1:8000/v1",
        session_api_key="sk_sess_test",
        project_root=str(project_root),
    )

    assert plan.command[:4] == ["opencode", "run", "--dir", str(project_root)]
    assert str(stale_root) not in plan.command


def test_detect_worker_adapter_reports_missing_command_without_verifying(monkeypatch):
    adapter = {
        "id": "opencode",
        "kind": "opencode",
        "config": {"verification_template": ["opencode", "run", "{prompt}"]},
    }
    monkeypatch.setattr("agile_ai_htb.worker_adapters.shutil.which", lambda command: None)

    diagnostics = detect_worker_adapter(adapter)

    assert diagnostics["installed"] is False
    assert diagnostics["callable"] is False
    assert diagnostics["command"] == "opencode"
    assert "not found on PATH" in diagnostics["failure_reason"]


def test_detect_worker_adapter_reports_callable_version_without_launch_verification(monkeypatch):
    adapter = {
        "id": "opencode",
        "kind": "opencode",
        "config": {"verification_template": ["opencode", "run", "{prompt}"]},
    }
    monkeypatch.setattr("agile_ai_htb.worker_adapters.shutil.which", lambda command: "/usr/local/bin/opencode")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout="opencode 1.2.3", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    diagnostics = detect_worker_adapter(adapter)

    assert diagnostics["installed"] is True
    assert diagnostics["callable"] is True
    assert diagnostics["executable"] == "/usr/local/bin/opencode"
    assert diagnostics["version"] == "opencode 1.2.3"
    assert diagnostics["failure_reason"] is None


def test_discover_worker_models_updates_adapter_from_native_json_without_proxy_env(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(tmp_path),
        supported_models=[],
    )
    plans = []

    def fake_runner(plan):
        plans.append(plan)
        return subprocess.CompletedProcess(
            plan.command,
            0,
            stdout='{"models":[{"id":"anthropic/claude-sonnet-4"},{"id":"openai/gpt-5.1"}]}',
            stderr="",
        )

    result = discover_worker_models(db_path, "opencode", runner=fake_runner)

    assert result.passed is True
    assert result.models == ["anthropic/claude-sonnet-4", "openai/gpt-5.1"]
    assert plans[0].env == {}
    assert plans[0].command == ["opencode", "models"]
    assert plans[0].metadata["purpose"] == "native_model_discovery"
    adapter = db.get_worker_adapter(db_path, "opencode")
    assert adapter["supported_models"] == []
    assert adapter["config"]["model_discovery"]["tracking_mode"] == "native"


def test_discover_worker_models_preserves_curated_allowed_models(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(tmp_path),
        supported_models=["openai/gpt-5.1"],
    )

    def fake_runner(plan):
        return subprocess.CompletedProcess(
            plan.command,
            0,
            stdout='{"models":[{"id":"openai/gpt-5.1"},{"id":"opencode/big-pickle"}]}',
            stderr="",
        )

    result = discover_worker_models(db_path, "opencode", runner=fake_runner)

    assert result.models == ["openai/gpt-5.1", "opencode/big-pickle"]
    adapter = db.get_worker_adapter(db_path, "opencode")
    assert adapter["config"]["model_discovery"]["models"] == ["openai/gpt-5.1", "opencode/big-pickle"]
    assert adapter["supported_models"] == ["openai/gpt-5.1"]


def test_discover_worker_models_preserves_empty_curated_allowed_models(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(tmp_path),
        config={"allowed_models_configured": True},
        supported_models=[],
    )

    def fake_runner(plan):
        return subprocess.CompletedProcess(
            plan.command,
            0,
            stdout='{"models":[{"id":"openai/gpt-5.1"},{"id":"opencode/big-pickle"}]}',
            stderr="",
        )

    discover_worker_models(db_path, "opencode", runner=fake_runner)

    assert db.get_worker_adapter(db_path, "opencode")["supported_models"] == []


def test_discover_worker_models_reports_failure_without_overwriting_models(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    before = db.get_worker_adapter(db_path, "opencode")["supported_models"]

    def fake_runner(plan):
        return subprocess.CompletedProcess(plan.command, 1, stdout="", stderr="secret sk_bad_key")

    result = discover_worker_models(db_path, "opencode", runner=fake_runner)

    assert result.passed is False
    assert "Model discovery command failed." in result.reasons
    assert "No Worker Harness models were discovered natively." in result.reasons
    assert "sk_bad_key" not in str(result.evidence)
    assert db.get_worker_adapter(db_path, "opencode")["supported_models"] == before


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
            metadata={"timeout_seconds": 123},
        )
    )

    assert result.returncode == 0
    assert calls[0][1]["env"]["AGILE_AI_HTB_OVERRIDE"] == "from-plan"
    assert calls[0][1]["env"]["AGILE_AI_HTB_INHERITED"] == "overridden"
    assert os.environ["PATH"] == calls[0][1]["env"]["PATH"]
    assert calls[0][1]["timeout"] == 123


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
