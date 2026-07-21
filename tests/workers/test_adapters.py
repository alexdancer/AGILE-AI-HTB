import os
import subprocess
from pathlib import Path

from foreman_ai_hq import db
from foreman_ai_hq.worker_adapters import (
    CommandPlan,
    detect_worker_adapter,
    discovered_worker_model_ids,
    discover_worker_models,
    get_adapter_builder,
    redact_command_plan,
    subprocess_runner,
)
from foreman_ai_hq.worker_model_allowlist import allowed_worker_model_ids


CLAUDE_CODE_CURATED_MODELS = [
    "claude-opus-4-8",
    "claude-sonnet-5",
    "claude-haiku-4-5",
]
PREVIOUS_CLAUDE_CODE_CURATED_MODELS = [
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-opus-4-6",
    "claude-sonnet-5",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
]
CODEX_CURATED_MODELS = ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"]


def test_init_db_seeds_worker_adapter_presets_idempotently_and_preserves_updates(tmp_path):
    db_path = tmp_path / "harness.db"

    db.init_db(db_path)
    with db.connect(db_path) as conn:
        conn.execute(
            """
            insert into worker_adapters (
                id, kind, name, config_json, supported_models_json, created_at, updated_at
            ) values ('hermes', 'hermes', 'Hermes', '{}', '[]', '2099-01-01T00:00:00Z', '2099-01-01T00:00:00Z')
            """
        )
    db.update_worker_adapter(
        db_path,
        "codex",
        workdir=str(tmp_path),
        config={"command": "codex", "env": {"OPENAI_API_KEY": "secret-value"}},
        supported_models=["gpt-5.4"],
        is_default=True,
    )
    db.init_db(db_path)

    adapters = db.list_worker_adapters(db_path)
    by_id = {adapter["id"]: adapter for adapter in adapters}
    assert {"claude_code", "codex", "opencode"}.issubset(by_id)
    assert "hermes" not in by_id
    assert by_id["codex"]["workdir"] == str(tmp_path)
    assert by_id["codex"]["supported_models"] == ["gpt-5.4"]
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
            "stdout": "FOREMAN_AI_HQ_ADAPTER_OK",
            "env": {"FOREMAN_AI_HQ_SESSION_API_KEY": "sk_sess_secret", "SAFE_FLAG": "ok"},
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
        "supported_models": ["gpt-5.6-terra"],
    }
    builder = get_adapter_builder(adapter)

    session_api_key = "test-session-key"
    plan = builder.build_verification_command(
        model="gpt-5.6-terra",
        prompt="Return sentinel",
        proxy_url="http://127.0.0.1:8000/v1",
        session_api_key=session_api_key,
    )
    safe = redact_command_plan(plan)

    assert builder.supports_model("gpt-5.6-terra") is True
    assert builder.supports_model("claude-3-haiku") is False
    assert plan.command == ["codex", "--model", "gpt-5.6-terra", "--prompt", "Return sentinel"]
    assert plan.cwd == Path(tmp_path)
    assert plan.env["OPENAI_BASE_URL"] == "http://127.0.0.1:8000/v1"
    assert plan.env["OPENAI_API_KEY"] == session_api_key
    assert session_api_key not in str(safe)
    assert safe["env"]["OPENAI_API_KEY"] == "***REDACTED***"


def test_codex_native_commands_use_exec_json_model_flag(tmp_path):
    adapter = {
        "id": "codex",
        "kind": "codex",
        "name": "Codex CLI",
        "workdir": str(tmp_path),
        "config": {"command": "codex", "launch_template": ["codex"]},
        "supported_models": ["gpt-5.4"],
    }
    builder = get_adapter_builder(adapter)

    verification_plan = builder.build_native_verification_command(model="gpt-5.4", prompt="Return sentinel")
    launch_plan = builder.build_native_launch_command(
        model="gpt-5.4",
        task_prompt="Implement the DEMO_2099 task.",
        project_root=str(tmp_path),
    )

    assert verification_plan.command == [
        "codex",
        "exec",
        "--json",
        "--skip-git-repo-check",
        "-m",
        "gpt-5.4",
        "Return sentinel",
    ]
    assert launch_plan.command == [
        "codex",
        "exec",
        "--json",
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "-m",
        "gpt-5.4",
        "--cd",
        str(tmp_path),
        "Implement the DEMO_2099 task.",
    ]
    assert "run" not in verification_plan.command
    assert "--format" not in verification_plan.command
    assert launch_plan.cwd == Path(tmp_path)
    assert launch_plan.metadata["project_root"] == str(tmp_path)
    assert launch_plan.metadata["timeout_seconds"] == 600
    safe = redact_command_plan(launch_plan)
    assert "Implement the DEMO_2099 task." not in str(safe)
    assert safe["command"][-1] == "***PROMPT_REDACTED:29 chars***"
    assert safe["metadata"]["prompt_redacted"] is True


def test_codex_native_template_injects_trust_bypass_and_project_root(tmp_path):
    adapter = {
        "id": "codex",
        "kind": "codex",
        "name": "Codex CLI",
        "workdir": str(tmp_path / "stale"),
        "config": {
            "native_launch_template": ["codex", "exec", "-m", "{model}", "{prompt}"],
            "native_verification_template": ["codex", "exec", "-m", "{model}", "{prompt}"],
        },
        "supported_models": ["gpt-5.4"],
    }
    builder = get_adapter_builder(adapter)

    verification_plan = builder.build_native_verification_command(model="gpt-5.4", prompt="Return sentinel")
    launch_plan = builder.build_native_launch_command(
        model="gpt-5.4",
        task_prompt="Implement task.",
        project_root=str(tmp_path),
    )

    assert verification_plan.command[:4] == ["codex", "exec", "--json", "--skip-git-repo-check"]
    assert launch_plan.command[:4] == ["codex", "exec", "--json", "--skip-git-repo-check"]
    assert launch_plan.command[4:6] == ["--sandbox", "workspace-write"]
    assert launch_plan.command[-3:] == ["--cd", str(tmp_path), "Implement task."]
    assert str(tmp_path / "stale") not in launch_plan.command


def test_codex_native_custom_executable_template_is_normalized(tmp_path):
    codex = tmp_path / "bin" / "codex"
    adapter = {
        "id": "codex",
        "kind": "codex",
        "name": "Codex CLI",
        "workdir": str(tmp_path / "stale"),
        "config": {
            "native_launch_template": [str(codex), "exec", "-m", "{model}", "{prompt}"],
            "native_verification_template": [str(codex), "exec", "-m", "{model}", "{prompt}"],
        },
        "supported_models": ["gpt-5.4"],
    }
    builder = get_adapter_builder(adapter)

    verification_plan = builder.build_native_verification_command(model="gpt-5.4", prompt="Return sentinel")
    launch_plan = builder.build_native_launch_command(model="gpt-5.4", task_prompt="Implement task.", project_root=str(tmp_path))

    assert verification_plan.command[:4] == [str(codex), "exec", "--json", "--skip-git-repo-check"]
    assert launch_plan.command[:4] == [str(codex), "exec", "--json", "--skip-git-repo-check"]
    assert launch_plan.command[4:6] == ["--sandbox", "workspace-write"]
    assert launch_plan.command[-3:] == ["--cd", str(tmp_path), "Implement task."]


def test_codex_native_launch_rewrites_read_only_sandbox(tmp_path):
    adapter = {
        "id": "codex",
        "kind": "codex",
        "name": "Codex CLI",
        "workdir": str(tmp_path),
        "config": {"native_launch_template": ["codex", "exec", "--sandbox", "read-only", "-m", "{model}", "{prompt}"]},
        "supported_models": ["gpt-5.4"],
    }

    plan = get_adapter_builder(adapter).build_native_launch_command(
        model="gpt-5.4",
        task_prompt="Implement task.",
        project_root=str(tmp_path),
    )

    sandbox_index = plan.command.index("--sandbox")
    assert plan.command[sandbox_index + 1] == "workspace-write"


def test_worker_adapter_template_can_reference_session_api_key(tmp_path):
    adapter = {
        "id": "custom_proxy_worker",
        "kind": "custom_proxy_worker",
        "name": "Custom Proxy Worker",
        "workdir": str(tmp_path),
        "config": {
            "verification_template": [
                "worker-cli",
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
        "worker-cli",
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
    assert plan.env["FOREMAN_AI_HQ_SESSION_API_KEY"] == "sk_sess_test"


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
        prompt="Return FOREMAN_AI_HQ_ADAPTER_OK",
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
        "Return FOREMAN_AI_HQ_ADAPTER_OK",
    ]
    assert plan.cwd == Path(tmp_path)


def test_claude_code_native_verification_defaults_to_stream_json_verbose_with_budget(tmp_path):
    adapter = {
        "id": "claude_code",
        "kind": "claude_code",
        "name": "Claude Code",
        "workdir": str(tmp_path),
        "config": {},
        "supported_models": ["sonnet"],
    }

    plan = get_adapter_builder(adapter).build_native_verification_command(
        model="sonnet",
        prompt="Return FOREMAN_AI_HQ_ADAPTER_OK",
    )

    assert plan.command == [
        "claude",
        "-p",
        "--model",
        "sonnet",
        "--output-format",
        "stream-json",
        "--verbose",
        "--max-budget-usd",
        "0.10",
        "Return FOREMAN_AI_HQ_ADAPTER_OK",
    ]
    assert plan.cwd == Path(tmp_path)
    assert plan.env == {}
    assert plan.metadata["tracking_mode"] == "native_usage"


def test_claude_code_native_launch_template_uses_configured_budget_cap(tmp_path):
    adapter = {
        "id": "claude_code",
        "kind": "claude_code",
        "name": "Claude Code",
        "workdir": str(tmp_path),
        "config": {"launch_max_budget_usd": "0.25"},
        "supported_models": ["sonnet"],
    }

    plan = get_adapter_builder(adapter).build_native_launch_command(
        model="sonnet",
        task_prompt="Implement DEMO_2099 task.",
    )

    assert plan.command == [
        "claude",
        "-p",
        "--model",
        "sonnet",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        "acceptEdits",
        "--allowedTools",
        "Bash,Write,Edit,MultiEdit",
        "--max-budget-usd",
        "0.25",
        "Implement DEMO_2099 task.",
    ]
    assert plan.metadata["usage_source"] == "native_usage"
    assert plan.metadata["timeout_seconds"] == 600


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
    monkeypatch.setattr("foreman_ai_hq.worker_adapters.shutil.which", lambda command: None)

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
    monkeypatch.setattr("foreman_ai_hq.worker_adapters.shutil.which", lambda command: "/usr/local/bin/opencode")

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


def test_discover_claude_code_models_uses_curated_inventory_without_subprocess(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    calls = []

    def fake_runner(plan):
        calls.append(plan)
        raise AssertionError("claude discovery must not launch a subprocess")

    result = discover_worker_models(db_path, "claude_code", runner=fake_runner)

    assert result.passed is True
    assert result.models == CLAUDE_CODE_CURATED_MODELS
    assert calls == []
    adapter = db.get_worker_adapter(db_path, "claude_code")
    assert adapter["config"]["model_discovery"]["tracking_mode"] == "curated"
    assert adapter["config"]["model_discovery"]["models"] == CLAUDE_CODE_CURATED_MODELS
    assert discovered_worker_model_ids(adapter) == CLAUDE_CODE_CURATED_MODELS


def test_discover_claude_code_models_preserves_allowed_subset(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "claude_code",
        config={"allowed_models_configured": True},
        supported_models=["claude-sonnet-5"],
    )

    result = discover_worker_models(db_path, "claude_code", runner=lambda plan: None)

    assert result.models == CLAUDE_CODE_CURATED_MODELS
    assert db.get_worker_adapter(db_path, "claude_code")["supported_models"] == ["claude-sonnet-5"]


def test_discover_codex_models_uses_curated_inventory_without_subprocess(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)

    def fail_if_called(plan):
        raise AssertionError("codex discovery must not launch a subprocess")

    result = discover_worker_models(db_path, "codex", runner=fail_if_called)

    assert result.passed is True
    assert result.models == CODEX_CURATED_MODELS
    assert result.evidence["tracking_mode"] == "curated"
    assert discovered_worker_model_ids(db.get_worker_adapter(db_path, "codex")) == CODEX_CURATED_MODELS


def test_codex_curated_discovery_clears_unapproved_legacy_seeded_models(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(db_path, "codex", supported_models=["gpt-5.1-codex", "openai/gpt-4.1-mini"])

    before = db.get_worker_adapter(db_path, "codex")
    assert allowed_worker_model_ids(before) == []

    discover_worker_models(db_path, "codex", runner=lambda plan: (_ for _ in ()).throw(AssertionError("must not run")))

    after = db.get_worker_adapter(db_path, "codex")
    assert after["supported_models"] == []
    assert discovered_worker_model_ids(after) == CODEX_CURATED_MODELS


def test_codex_single_stale_model_is_not_operator_approved(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(db_path, "codex", supported_models=["5.4"])

    before = db.get_worker_adapter(db_path, "codex")
    assert allowed_worker_model_ids(before) == []

    discover_worker_models(db_path, "codex", runner=lambda plan: (_ for _ in ()).throw(AssertionError("must not run")))

    after = db.get_worker_adapter(db_path, "codex")
    assert after["supported_models"] == []


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


def test_discover_worker_models_rejects_successful_prose_stdout(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)

    def fake_runner(plan):
        return subprocess.CompletedProcess(
            plan.command,
            0,
            stdout="Here's the model landscape in this codebase:\n## Control-plane models\nLet me know and I'll dig in.",
            stderr="",
        )

    result = discover_worker_models(db_path, "opencode", runner=fake_runner)

    assert result.passed is False
    assert result.models == []
    assert db.get_worker_adapter(db_path, "opencode")["config"]["model_discovery"]["models"] == []


def test_discover_worker_models_accepts_valid_plain_line_output(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)

    result = discover_worker_models(
        db_path,
        "opencode",
        runner=lambda plan: subprocess.CompletedProcess(
            plan.command,
            0,
            stdout="openai/gpt-5.1\nopencode/big-pickle\n",
            stderr="",
        ),
    )

    assert result.passed is True
    assert result.models == ["openai/gpt-5.1", "opencode/big-pickle"]


def test_discover_worker_models_reports_failure_without_overwriting_models(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    before = db.get_worker_adapter(db_path, "opencode")["supported_models"]

    def fake_runner(plan):
        return subprocess.CompletedProcess(plan.command, 1, stdout="secret sk_bad_key", stderr="secret sk_bad_key")

    result = discover_worker_models(db_path, "opencode", runner=fake_runner)

    assert result.passed is False
    assert result.models == []
    assert "Model discovery command failed." in result.reasons
    assert "No Worker Harness models were discovered natively." in result.reasons
    assert "sk_bad_key" not in str(result.evidence)
    adapter = db.get_worker_adapter(db_path, "opencode")
    assert adapter["supported_models"] == before
    assert adapter["config"]["model_discovery"]["models"] == []
    assert "sk_bad_key" not in str(adapter["config"]["model_discovery"])


def test_claude_code_model_discovery_failure_does_not_convert_stdout_to_models(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    adapter = db.get_worker_adapter(db_path, "claude_code")

    result = discover_worker_models(db_path, "claude_code", runner=lambda plan: None)

    assert result.passed is True
    assert result.models == CLAUDE_CODE_CURATED_MODELS
    assert discovered_worker_model_ids(adapter) == CLAUDE_CODE_CURATED_MODELS


def test_claude_code_curated_discovery_clears_unapproved_legacy_seeded_models(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    legacy_models = ["claude-3-5-sonnet-latest", "claude-3-5-sonnet-20240620", "claude-3-haiku-20240307"]
    db.update_worker_adapter(db_path, "claude_code", supported_models=legacy_models)

    before = db.get_worker_adapter(db_path, "claude_code")
    assert before["supported_models"] == legacy_models
    assert allowed_worker_model_ids(before) == []
    assert get_adapter_builder(before).supports_model("claude-3-5-sonnet-latest") is False

    discover_worker_models(db_path, "claude_code", runner=lambda plan: (_ for _ in ()).throw(AssertionError("must not run")))

    after = db.get_worker_adapter(db_path, "claude_code")
    assert after["supported_models"] == []
    assert allowed_worker_model_ids(after) == []
    assert discovered_worker_model_ids(after) == CLAUDE_CODE_CURATED_MODELS


def test_claude_code_curated_discovery_clears_previous_seeded_models_after_inventory_update(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(db_path, "claude_code", supported_models=PREVIOUS_CLAUDE_CODE_CURATED_MODELS)

    before = db.get_worker_adapter(db_path, "claude_code")
    assert before["supported_models"] == PREVIOUS_CLAUDE_CODE_CURATED_MODELS
    assert allowed_worker_model_ids(before) == []
    assert get_adapter_builder(before).supports_model("claude-sonnet-4-6") is False

    discover_worker_models(db_path, "claude_code", runner=lambda plan: (_ for _ in ()).throw(AssertionError("must not run")))

    after = db.get_worker_adapter(db_path, "claude_code")
    assert after["supported_models"] == []
    assert allowed_worker_model_ids(after) == []
    assert discovered_worker_model_ids(after) == CLAUDE_CODE_CURATED_MODELS


def test_claude_code_curated_discovery_prunes_approved_subset_to_curated_models(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    adapter = db.get_worker_adapter(db_path, "claude_code")
    config = {**adapter["config"], "allowed_models_configured": True}
    db.update_worker_adapter(
        db_path,
        "claude_code",
        config=config,
        supported_models=["claude-3-5-sonnet-latest", "claude-opus-4-8"],
    )

    discover_worker_models(db_path, "claude_code", runner=lambda plan: (_ for _ in ()).throw(AssertionError("must not run")))

    after = db.get_worker_adapter(db_path, "claude_code")
    assert after["supported_models"] == ["claude-opus-4-8"]
    assert allowed_worker_model_ids(after) == ["claude-opus-4-8"]


def test_redact_command_plan_redacts_secret_flag_values_without_over_redacting(tmp_path):
    safe = redact_command_plan(
        CommandPlan(
            command=[
                "tool",
                "--api-key",
                "abc123",
                "--model",
                "5.4",
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
        "5.4",
        "--token=***REDACTED***",
        "-H",
        "***REDACTED***",
        "--prompt",
        "***REDACTED***",
    ]


def test_subprocess_runner_inherits_environment_and_applies_overrides_and_timeout(monkeypatch, tmp_path):
    monkeypatch.setenv("FOREMAN_AI_HQ_INHERITED", "from-parent")
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = subprocess_runner(
        CommandPlan(
            command=["worker", "verify"],
            cwd=tmp_path,
            env={"FOREMAN_AI_HQ_OVERRIDE": "from-plan", "FOREMAN_AI_HQ_INHERITED": "overridden"},
            metadata={"timeout_seconds": 123},
        )
    )

    assert result.returncode == 0
    assert calls[0][1]["env"]["FOREMAN_AI_HQ_OVERRIDE"] == "from-plan"
    assert calls[0][1]["env"]["FOREMAN_AI_HQ_INHERITED"] == "overridden"
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
