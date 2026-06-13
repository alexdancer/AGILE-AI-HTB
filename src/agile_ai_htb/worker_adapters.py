from __future__ import annotations

import hashlib
import os
import re
import secrets
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from agile_ai_htb import db

SENTINEL_RESPONSE = "AGILE_AI_HTB_ADAPTER_OK"
SENTINEL_PROMPT = f"Reply exactly {SENTINEL_RESPONSE}"
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
        guardrail_overrides={"verification": {"adapter_id": adapter_id}},
        status="running",
    )
    builder = get_adapter_builder(adapter)
    reasons: list[str] = []
    if not builder.supports_model(model):
        reasons.append("Selected model is not supported by this adapter.")
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
    stdout = _result_field(completed, "stdout")
    returncode = int(_result_field(completed, "returncode", 0) or 0)
    sentinel_matched = stdout.strip() == SENTINEL_RESPONSE
    if returncode != 0:
        reasons.append("Adapter verification command failed.")
    if not sentinel_matched:
        reasons.append("Adapter did not return exact verification sentinel.")
    if token_recorder is not None:
        token_recorder(session["id"])
    token_recorded = db.has_adapter_verification_token(database_path, session_id=session["id"], model=model)
    if not token_recorded:
        reasons.append("No adapter_verification token row was recorded for selected model.")

    evidence = {
        "session_id": session["id"],
        "model": model,
        "returncode": returncode,
        "stdout": stdout.strip(),
        "stderr": _redact_value(str(_result_field(completed, "stderr", ""))),
        "sentinel_matched": sentinel_matched,
        "token_recorded": token_recorded,
        "command_plan": redact_command_plan(plan),
    }
    passed = not reasons
    adapter = db.mark_worker_adapter_verification(database_path, adapter_id, verified=passed, evidence=evidence)
    db.update_session_status(database_path, session["id"], "completed" if passed else "failed")
    return VerificationResult(passed, adapter_id, session["id"], reasons, adapter["verification_evidence"])


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
