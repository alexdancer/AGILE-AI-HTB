from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from agile_ai_htb import db

SENTINEL_RESPONSE = "AGILE_AI_HTB_ADAPTER_OK"
SENTINEL_PROMPT = (
    "Verification only. Do not read files, write files, run tools, or inspect the repository. "
    f"Reply exactly {SENTINEL_RESPONSE}"
)
SECRET_ENV_TERMS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "AUTHORIZATION")
SECRET_VALUE_PATTERN = re.compile("s" "k_" r"[A-Za-z0-9_\-.]+")
SUBPROCESS_RUNNER_TIMEOUT_SECONDS = 60
SECRET_COMMAND_FLAGS = {
    "--api-key",
    "--apikey",
    "--token",
    "--secret",
    "--password",
    "--authorization",
}


@dataclass(frozen=True)
class CommandPlan:
    command: list[str]
    cwd: Path | None
    env: dict[str, str]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    adapter_id: str
    session_id: str
    reasons: list[str]
    evidence: dict[str, Any]


@dataclass(frozen=True)
class ModelDiscoveryResult:
    passed: bool
    adapter_id: str
    models: list[str]
    reasons: list[str]
    evidence: dict[str, Any]


@dataclass(frozen=True)
class NativeUsageEvidence:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    raw_usage: dict[str, Any]


class Runner(Protocol):
    def __call__(self, plan: CommandPlan) -> Any: ...


class WorkerAdapterBuilder:
    api_key_env = "OPENAI_API_KEY"
    base_url_env = "OPENAI_BASE_URL"

    def __init__(self, adapter: dict[str, Any]) -> None:
        self.adapter = adapter
        self.config = adapter.get("config", {})

    def supports_model(self, model: str) -> bool:
        supported = self.adapter.get("supported_models") or []
        return not supported or model in supported

    def build_verification_command(
        self,
        *,
        model: str,
        prompt: str,
        proxy_url: str,
        session_api_key: str,
    ) -> CommandPlan:
        return self._build_command(
            template_key="verification_template",
            fallback=[self.config.get("command") or self.adapter["kind"], "{prompt}"],
            model=model,
            prompt=prompt,
            proxy_url=proxy_url,
            session_api_key=session_api_key,
            purpose="adapter_verification",
        )

    def build_native_verification_command(
        self,
        *,
        model: str,
        prompt: str,
    ) -> CommandPlan:
        template = self.config.get("native_verification_template") or self._default_native_verification_template()
        command = [str(part).format(model=model, prompt=prompt) for part in template]
        workdir = self.adapter.get("workdir")
        return CommandPlan(
            command=command,
            cwd=Path(workdir) if workdir else None,
            env={},
            metadata={
                "adapter_id": self.adapter["id"],
                "kind": self.adapter["kind"],
                "model": model,
                "purpose": "native_adapter_verification",
                "tracking_mode": "native_usage",
            },
        )

    def _default_native_verification_template(self) -> list[str]:
        command = self.config.get("command") or self.adapter["kind"]
        return [str(command), "run", "--model", "{model}", "--format", "json", "{prompt}"]

    def build_native_launch_command(
        self,
        *,
        model: str,
        task_prompt: str,
    ) -> CommandPlan:
        template = self.config.get("native_launch_template") or self._default_native_launch_template()
        command = [str(part).format(model=model, prompt=task_prompt) for part in template]
        workdir = self.adapter.get("workdir")
        return CommandPlan(
            command=command,
            cwd=Path(workdir) if workdir else None,
            env={},
            metadata={
                "adapter_id": self.adapter["id"],
                "kind": self.adapter["kind"],
                "model": model,
                "purpose": "task_launch",
                "tracking_mode": "native_usage",
                "usage_source": "native_usage",
            },
        )

    def _default_native_launch_template(self) -> list[str]:
        command = self.config.get("command") or self.adapter["kind"]
        return [str(command), "run", "--model", "{model}", "--format", "json", "{prompt}"]

    def build_launch_command(
        self,
        *,
        model: str,
        task_prompt: str,
        proxy_url: str,
        session_api_key: str,
    ) -> CommandPlan:
        return self._build_command(
            template_key="launch_template",
            fallback=[self.config.get("command") or self.adapter["kind"], "{prompt}"],
            model=model,
            prompt=task_prompt,
            proxy_url=proxy_url,
            session_api_key=session_api_key,
            purpose="task_launch",
        )

    def _build_command(
        self,
        *,
        template_key: str,
        fallback: list[str],
        model: str,
        prompt: str,
        proxy_url: str,
        session_api_key: str,
        purpose: str,
    ) -> CommandPlan:
        template = self.config.get(template_key) or fallback
        command = [str(part).format(model=model, prompt=prompt, proxy_url=proxy_url) for part in template]
        env = self._env(proxy_url=proxy_url, session_api_key=session_api_key)
        for key, value in (self.config.get("env") or {}).items():
            if not _is_secret_name(key):
                env[str(key)] = str(value)
        workdir = self.adapter.get("workdir")
        return CommandPlan(
            command=command,
            cwd=Path(workdir) if workdir else None,
            env=env,
            metadata={"adapter_id": self.adapter["id"], "kind": self.adapter["kind"], "model": model, "purpose": purpose},
        )

    def _env(self, *, proxy_url: str, session_api_key: str) -> dict[str, str]:
        return {
            self.base_url_env: proxy_url,
            self.api_key_env: session_api_key,
            "AGILE_AI_HTB_PROXY_URL": proxy_url,
            "AGILE_AI_HTB_SESSION_API_KEY": session_api_key,
        }


class ClaudeCodeAdapterBuilder(WorkerAdapterBuilder):
    api_key_env = "ANTHROPIC_API_KEY"
    base_url_env = "ANTHROPIC_BASE_URL"


class CodexAdapterBuilder(WorkerAdapterBuilder):
    api_key_env = "OPENAI_API_KEY"
    base_url_env = "OPENAI_BASE_URL"


class OpenCodeAdapterBuilder(WorkerAdapterBuilder):
    api_key_env = "OPENAI_API_KEY"
    base_url_env = "OPENAI_BASE_URL"


BUILDERS = {
    "claude_code": ClaudeCodeAdapterBuilder,
    "codex": CodexAdapterBuilder,
    "opencode": OpenCodeAdapterBuilder,
}


def get_adapter_builder(adapter: dict[str, Any]) -> WorkerAdapterBuilder:
    return BUILDERS.get(adapter.get("kind"), WorkerAdapterBuilder)(adapter)


def detect_worker_adapter(adapter: dict[str, Any]) -> dict[str, Any]:
    command_name = _adapter_command_name(adapter)
    executable = shutil.which(command_name) if command_name else None
    if not command_name:
        return {
            "installed": False,
            "callable": False,
            "command": None,
            "executable": None,
            "version": None,
            "failure_reason": "No adapter command is configured.",
        }
    if executable is None:
        return {
            "installed": False,
            "callable": False,
            "command": command_name,
            "executable": None,
            "version": None,
            "failure_reason": f"Command '{command_name}' was not found on PATH.",
        }

    completed = subprocess.run(
        [command_name, "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    output = (completed.stdout or completed.stderr or "").strip()
    if completed.returncode != 0:
        return {
            "installed": True,
            "callable": False,
            "command": command_name,
            "executable": executable,
            "version": output or None,
            "failure_reason": f"Command '{command_name} --version' exited with {completed.returncode}.",
        }
    return {
        "installed": True,
        "callable": True,
        "command": command_name,
        "executable": executable,
        "version": output or None,
        "failure_reason": None,
    }


def discover_worker_models(
    database_path: Path | str,
    adapter_id: str,
    *,
    runner: Runner | None = None,
) -> ModelDiscoveryResult:
    adapter = db.get_worker_adapter(database_path, adapter_id)
    plan = _model_discovery_plan(adapter)
    reasons: list[str] = []
    try:
        completed = (runner or subprocess_runner)(plan)
    except Exception as exc:
        completed = subprocess.CompletedProcess(
            plan.command,
            127,
            stdout="",
            stderr=f"Failed to launch command {redact_command_plan(plan)['command'][0]!r}: {type(exc).__name__}",
        )
    stdout = str(_result_field(completed, "stdout", "") or "")
    stderr = str(_result_field(completed, "stderr", "") or "")
    returncode = int(_result_field(completed, "returncode", 0) or 0)
    models = _parse_discovered_models(stdout)
    if returncode != 0:
        reasons.append("Model discovery command failed.")
    if not models:
        reasons.append("No Worker Harness models were discovered natively.")
    evidence = {
        "returncode": returncode,
        "stdout": _redact_value(stdout.strip()),
        "stderr": _redact_value(stderr.strip()),
        "models": models,
        "command_plan": redact_command_plan(plan),
        "tracking_mode": "native",
    }
    if models:
        config = {**(adapter.get("config") or {}), "model_discovery": evidence}
        db.update_worker_adapter(database_path, adapter_id, config=config, supported_models=models)
    return ModelDiscoveryResult(not reasons, adapter_id, models, reasons, evidence)


def _adapter_command_name(adapter: dict[str, Any]) -> str | None:
    config = adapter.get("config") or {}
    command = config.get("command")
    if command:
        return str(command).split()[0]
    template = config.get("verification_template") or config.get("launch_template") or []
    if template:
        return str(template[0])
    return adapter.get("kind")


def _model_discovery_plan(adapter: dict[str, Any]) -> CommandPlan:
    config = adapter.get("config") or {}
    template = config.get("model_discovery_template") or _default_model_discovery_template(adapter)
    workdir = adapter.get("workdir")
    return CommandPlan(
        command=[str(part) for part in template],
        cwd=Path(workdir) if workdir else None,
        env={},
        metadata={"adapter_id": adapter["id"], "kind": adapter["kind"], "purpose": "native_model_discovery"},
    )


def _default_model_discovery_template(adapter: dict[str, Any]) -> list[str]:
    command = _adapter_command_name(adapter) or str(adapter.get("kind") or "worker")
    if adapter.get("kind") == "opencode":
        return [command, "models", "--json"]
    return [command, "models"]


def _parse_discovered_models(stdout: str) -> list[str]:
    text = stdout.strip()
    if not text:
        return []
    parsed: Any | None = None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    candidates = _models_from_json(parsed) if parsed is not None else []
    if not candidates:
        candidates = [line.strip() for line in text.splitlines() if line.strip() and not line.lower().startswith("model")]
    seen: set[str] = set()
    models: list[str] = []
    for candidate in candidates:
        model = str(candidate).strip()
        if not model or model in seen:
            continue
        seen.add(model)
        models.append(model)
    return models


def _models_from_json(value: Any) -> list[str]:
    if isinstance(value, list):
        models: list[str] = []
        for item in value:
            if isinstance(item, str):
                models.append(item)
            elif isinstance(item, dict):
                for key in ("id", "model", "name"):
                    if item.get(key):
                        models.append(str(item[key]))
                        break
        return models
    if isinstance(value, dict):
        for key in ("models", "data"):
            if key in value:
                return _models_from_json(value[key])
    return []


def redact_command_plan(plan: CommandPlan) -> dict[str, Any]:
    return {
        "command": _redact_command(plan.command),
        "cwd": str(plan.cwd) if plan.cwd else None,
        "env": {key: ("***REDACTED***" if _is_secret_name(key) else _redact_value(value)) for key, value in plan.env.items()},
        "metadata": dict(plan.metadata),
    }


def verify_worker_adapter(
    database_path: Path | str,
    adapter_id: str,
    *,
    model: str,
    proxy_url: str,
    tracking_mode: str = "proxy_governed",
    runner: Runner | None = None,
    token_recorder: Callable[[str], None] | None = None,
) -> VerificationResult:
    adapter = db.get_worker_adapter(database_path, adapter_id)
    session_api_key = f"sk_sess_{secrets.token_urlsafe(24)}"
    session = db.create_session(
        database_path,
        task_description=f"Worker adapter verification: {adapter['name']}",
        model=model,
        session_key_hash=hashlib.sha256(session_api_key.encode("utf-8")).hexdigest(),
        guardrail_overrides={"verification": {"adapter_id": adapter_id, "tracking_mode": tracking_mode}},
        status="running",
    )
    builder = get_adapter_builder(adapter)
    reasons: list[str] = []
    if tracking_mode not in {"proxy_governed", "native_usage"}:
        reasons.append("Unsupported adapter verification tracking mode.")
    if not builder.supports_model(model):
        reasons.append("Selected model is not supported by this adapter.")
    if tracking_mode == "native_usage":
        plan = builder.build_native_verification_command(model=model, prompt=SENTINEL_PROMPT)
    else:
        plan = builder.build_verification_command(
            model=model,
            prompt=SENTINEL_PROMPT,
            proxy_url=proxy_url,
            session_api_key=session_api_key,
        )
    if reasons:
        evidence = {
            "session_id": session["id"],
            "model": model,
            "tracking_mode": "observed_only",
            "tracking_authoritative": False,
            "preflight_failed": True,
            "reasons": list(reasons),
            "command_plan": redact_command_plan(plan),
        }
        adapter = db.mark_worker_adapter_verification(database_path, adapter_id, verified=False, evidence=evidence)
        db.update_session_status(database_path, session["id"], "failed")
        return VerificationResult(False, adapter_id, session["id"], reasons, adapter["verification_evidence"])

    try:
        completed = (runner or subprocess_runner)(plan)
    except Exception as exc:
        completed = subprocess.CompletedProcess(
            plan.command,
            127,
            stdout="",
            stderr=f"Failed to launch command {redact_command_plan(plan)['command'][0]!r}: {type(exc).__name__}",
        )
    stdout = str(_result_field(completed, "stdout") or "")
    returncode = int(_result_field(completed, "returncode", 0) or 0)
    sentinel_matched = _native_sentinel_matched(stdout) if tracking_mode == "native_usage" else stdout.strip() == SENTINEL_RESPONSE
    if returncode != 0:
        reasons.append("Adapter verification command failed.")
    if not sentinel_matched:
        reasons.append("Adapter did not return exact verification sentinel.")

    native_usage = _parse_native_usage_evidence(stdout, model=model) if tracking_mode == "native_usage" else None
    if tracking_mode == "native_usage":
        if native_usage is None:
            reasons.append("No trustworthy native usage evidence was emitted for selected model.")
        else:
            db.record_token_turn(
                database_path,
                session_id=session["id"],
                usage_kind="adapter_verification",
                model=model,
                prompt_tokens=native_usage.prompt_tokens,
                completion_tokens=native_usage.completion_tokens,
                cost=native_usage.cost,
                raw_usage={
                    **native_usage.raw_usage,
                    "total_tokens": native_usage.total_tokens,
                    "usage_source": "native_usage",
                    "tracking_mode": "native_usage",
                    "worker_harness": adapter.get("kind"),
                },
            )
    elif token_recorder is not None:
        token_recorder(session["id"])

    token_recorded = db.has_adapter_verification_token(database_path, session_id=session["id"], model=model)
    if not token_recorded:
        reasons.append("No adapter_verification token row was recorded for selected model.")
    resolved_tracking_mode = tracking_mode if token_recorded else "observed_only"

    evidence = {
        "session_id": session["id"],
        "model": model,
        "tracking_mode": resolved_tracking_mode,
        "tracking_authoritative": resolved_tracking_mode in {"proxy_governed", "native_usage"},
        "returncode": returncode,
        "stdout": _redact_value(stdout.strip()),
        "stderr": _redact_value(str(_result_field(completed, "stderr", ""))),
        "sentinel_matched": sentinel_matched,
        "token_recorded": token_recorded,
        "command_plan": redact_command_plan(plan),
    }
    if native_usage is not None:
        evidence["native_usage"] = native_usage.raw_usage
    passed = not reasons
    adapter = db.mark_worker_adapter_verification(database_path, adapter_id, verified=passed, evidence=evidence)
    db.update_session_status(database_path, session["id"], "completed" if passed else "failed")
    return VerificationResult(passed, adapter_id, session["id"], reasons, adapter["verification_evidence"])


def _native_sentinel_matched(stdout: str) -> bool:
    if stdout.strip() == SENTINEL_RESPONSE:
        return True
    return any(SENTINEL_RESPONSE in str(value) for value in _walk_json_values(_parse_json_stream(stdout)))


def _parse_native_usage_evidence(stdout: str, *, model: str) -> NativeUsageEvidence | None:
    for item in _walk_json_dicts(_parse_json_stream(stdout)):
        usage = _usage_payload(item)
        if not usage:
            continue
        usage_model = _usage_model(item, usage)
        if usage_model != model:
            continue
        prompt_tokens = _int_from_any(
            usage.get("prompt_tokens")
            or usage.get("input_tokens")
            or usage.get("input")
            or usage.get("tokens_in")
        )
        completion_tokens = _int_from_any(
            usage.get("completion_tokens")
            or usage.get("output_tokens")
            or usage.get("output")
            or usage.get("tokens_out")
        )
        total_tokens = _int_from_any(usage.get("total_tokens") or usage.get("total"))
        if total_tokens <= 0:
            total_tokens = prompt_tokens + completion_tokens
        if total_tokens <= 0:
            continue
        return NativeUsageEvidence(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=_float_from_any(usage.get("cost") or usage.get("cost_usd") or usage.get("usd")),
            raw_usage={"model": usage_model, "usage": usage},
        )
    return None


def _parse_json_stream(text: str) -> list[Any]:
    stripped = text.strip()
    if not stripped:
        return []
    try:
        return [json.loads(stripped)]
    except json.JSONDecodeError:
        pass
    values: list[Any] = []
    for line in stripped.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            values.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return values


def _walk_json_values(values: list[Any]) -> list[Any]:
    walked: list[Any] = []
    for value in values:
        walked.append(value)
        if isinstance(value, dict):
            walked.extend(_walk_json_values(list(value.values())))
        elif isinstance(value, list):
            walked.extend(_walk_json_values(value))
    return walked


def _walk_json_dicts(values: list[Any]) -> list[dict[str, Any]]:
    return [value for value in _walk_json_values(values) if isinstance(value, dict)]


def _usage_payload(item: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("usage", "tokens", "token_usage", "cost"):
        candidate = item.get(key)
        if isinstance(candidate, dict) and any(_looks_like_usage_key(usage_key) for usage_key in candidate):
            return candidate
    if any(_looks_like_usage_key(key) for key in item):
        return item
    return None


def _usage_model(item: dict[str, Any], usage: dict[str, Any]) -> str | None:
    for container in (usage, item):
        for key in ("model", "model_id", "modelID"):
            if container.get(key):
                return str(container[key])
    return None


def _looks_like_usage_key(key: str) -> bool:
    normalized = key.lower()
    return normalized in {
        "prompt_tokens",
        "completion_tokens",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "tokens_in",
        "tokens_out",
        "cost_usd",
    }


def _int_from_any(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        value = value.replace(",", "").strip()
        if value.endswith("K"):
            return int(float(value[:-1]) * 1000)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _float_from_any(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "").strip()
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def subprocess_runner(plan: CommandPlan) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            plan.command,
            cwd=str(plan.cwd) if plan.cwd else None,
            env={**os.environ, **plan.env},
            capture_output=True,
            text=True,
            check=False,
            timeout=SUBPROCESS_RUNNER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        stderr = exc.stderr or ""
        timeout_message = f"Command timed out after {SUBPROCESS_RUNNER_TIMEOUT_SECONDS} seconds."
        return subprocess.CompletedProcess(
            plan.command,
            124,
            stdout=exc.output or "",
            stderr=f"{stderr}\n{timeout_message}" if stderr else timeout_message,
        )
    except OSError as exc:
        command_name = _redact_value(str(plan.command[0])) if plan.command else "<empty>"
        error_text = getattr(exc, "strerror", None) or str(exc)
        return subprocess.CompletedProcess(
            plan.command,
            127,
            stdout="",
            stderr=f"Failed to launch command {command_name!r}: {type(exc).__name__}: {_redact_value(str(error_text))}",
        )


def _result_field(result: Any, field: str, default: Any = "") -> Any:
    if isinstance(result, dict):
        return result.get(field, default)
    return getattr(result, field, default)


def _is_secret_name(name: str) -> bool:
    return any(term in name.upper() for term in SECRET_ENV_TERMS)


def _redact_command(command: list[str]) -> list[str]:
    redacted: list[str] = []
    redact_next = False
    previous_was_header_flag = False
    for part in command:
        if redact_next:
            redacted.append("***REDACTED***")
            redact_next = False
            previous_was_header_flag = False
            continue

        if previous_was_header_flag and part.lower().startswith("authorization:"):
            redacted.append("***REDACTED***")
            previous_was_header_flag = False
            continue
        previous_was_header_flag = False

        flag, separator, _value = part.partition("=")
        lowered_flag = flag.lower()
        if separator and lowered_flag in SECRET_COMMAND_FLAGS:
            redacted.append(f"{flag}=***REDACTED***")
            continue
        if lowered_flag in SECRET_COMMAND_FLAGS:
            redacted.append(_redact_value(part))
            redact_next = True
            continue
        if part == "-H":
            redacted.append(part)
            previous_was_header_flag = True
            continue
        redacted.append(_redact_value(part))
    return redacted


def _redact_value(value: str) -> str:
    if "secret" in value.lower():
        return "***REDACTED***"
    return SECRET_VALUE_PATTERN.sub("***REDACTED***", value)
