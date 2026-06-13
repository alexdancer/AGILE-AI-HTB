from __future__ import annotations

import hashlib
import os
import re
import secrets
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from agile_ai_htb import db
from agile_ai_htb.launch_guardrails import evaluate_launch_guardrails
from agile_ai_htb.worker_adapters import (
    Runner,
    get_adapter_builder,
    redact_command_plan,
    subprocess_runner,
)


def _harness_port() -> str:
    return os.environ.get("PORT", "8000")


DEFAULT_PROXY_URL = f"http://127.0.0.1:{_harness_port()}/v1"
LAUNCHABLE_TASK_STATUSES = {"Estimated", "Ready"}
SESSION_KEY_PATTERN = re.compile(r"sk_sess_[A-Za-z0-9_\-.]+")
SECRETISH_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"sk_[A-Za-z0-9_\-.]+"),
)


@dataclass(frozen=True)
class TaskLaunchBlocked(Exception):
    task: dict[str, Any]
    reasons: list[str]
    status_code: int = 409


@dataclass(frozen=True)
class TaskLaunchResult:
    task: dict[str, Any]
    session: dict[str, Any] | None
    launch_guardrails: dict[str, Any]

    def as_response(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "session": self.session,
            "launch_guardrails": self.launch_guardrails,
        }


def launch_task(
    database_path: Path | str,
    task_id: str,
    *,
    adapter_id: str | None,
    model: str | None,
    proxy_url: str | None,
    estimate_tokens: int | None = None,
    runner: Runner | None = None,
) -> TaskLaunchResult:
    task = db.get_task(database_path, task_id)
    manual_estimate_requested = estimate_tokens is not None and bool(model)

    if task.get("status") not in LAUNCHABLE_TASK_STATUSES:
        if manual_estimate_requested and _is_manual_estimate_required(task):
            task = _apply_manual_estimate(database_path, task, estimate_tokens, str(model))
        else:
            blocked = _mark_launch_status_blocked(
                database_path,
                task,
                ["Only Estimated or Ready tasks can launch."],
            )
            raise TaskLaunchBlocked(blocked, ["Only Estimated or Ready tasks can launch."])
    elif manual_estimate_requested:
        task = _apply_manual_estimate(database_path, task, estimate_tokens, str(model))

    if task.get("status") not in LAUNCHABLE_TASK_STATUSES:
        blocked = _mark_launch_status_blocked(
            database_path,
            task,
            ["Only Estimated or Ready tasks can launch."],
        )
        raise TaskLaunchBlocked(blocked, ["Only Estimated or Ready tasks can launch."])

    selected_model = model or task.get("recommended_model")
    selected_adapter_id = adapter_id or _default_adapter_id(database_path)
    selected_proxy_url = proxy_url or DEFAULT_PROXY_URL
    session_api_key = f"sk_sess_{secrets.token_urlsafe(24)}"

    if not selected_model:
        blocked = _mark_launch_blocked(database_path, task, ["Estimated model is required before launch."])
        raise TaskLaunchBlocked(blocked, ["Estimated model is required before launch."])
    if not task.get("estimate_tokens"):
        blocked = _mark_launch_blocked(database_path, task, ["Token estimate is required before launch."])
        raise TaskLaunchBlocked(blocked, ["Token estimate is required before launch."])
    if not selected_adapter_id:
        blocked = _mark_launch_blocked(database_path, task, ["No worker adapter is configured for launch."])
        raise TaskLaunchBlocked(blocked, ["No worker adapter is configured for launch."])

    guardrails = evaluate_launch_guardrails(
        database_path,
        adapter_id=selected_adapter_id,
        model=selected_model,
        session_api_key=session_api_key,
        proxy_url=selected_proxy_url,
    )
    if not guardrails.passed or guardrails.adapter is None:
        blocked = _mark_launch_blocked(database_path, task, guardrails.reasons)
        raise TaskLaunchBlocked(blocked, guardrails.reasons)

    session = db.create_session(
        database_path,
        task_description=task["description"],
        model=selected_model,
        session_key_hash=_hash_key(session_api_key),
        guardrail_overrides={"task_launch": {"task_id": task_id, "adapter_id": selected_adapter_id}},
        status="running",
    )
    builder = get_adapter_builder(guardrails.adapter)
    plan = builder.build_launch_command(
        model=selected_model,
        task_prompt=task["description"],
        proxy_url=selected_proxy_url,
        session_api_key=session_api_key,
    )
    plan = replace(
        plan,
        metadata={**plan.metadata, "session_id": session["id"], "task_id": task_id},
    )
    command_plan = redact_command_plan(plan)
    claimed = db.update_task(
        database_path,
        task_id,
        {
            "status": "Running",
            "session_id": session["id"],
            "metadata": {
                **task.get("metadata", {}),
                "launch_adapter_id": selected_adapter_id,
                "launch_model": selected_model,
                "launch_command_plan": command_plan,
            },
        },
    )

    try:
        completed = (runner or subprocess_runner)(plan)
    except Exception as exc:
        completed = subprocess.CompletedProcess(
            plan.command,
            127,
            stdout="",
            stderr=f"Failed to launch adapter runner: {type(exc).__name__}",
        )
    returncode = int(_result_field(completed, "returncode", 0) or 0)
    stdout = str(_result_field(completed, "stdout", ""))
    stderr = str(_result_field(completed, "stderr", ""))
    if returncode != 0:
        db.update_session_status(database_path, session["id"], "failed")
        failed = db.update_task(
            database_path,
            task_id,
            {
                "status": "Blocked",
                "session_id": session["id"],
                "metadata": {
                    **claimed.get("metadata", {}),
                    "launch_blocked_reason": "Worker adapter launch failed.",
                    "launch_guardrail_reasons": [],
                    "launch_returncode": returncode,
                    "launch_stderr": _safe_text(stderr),
                },
            },
        )
        raise TaskLaunchBlocked(failed, ["Worker adapter launch failed."])

    launched = db.update_task(
        database_path,
        task_id,
        {
            "status": "Running",
            "session_id": session["id"],
            "metadata": {
                **claimed.get("metadata", {}),
                "launch_returncode": returncode,
                "launch_stdout": _safe_text(stdout),
            },
        },
    )
    return TaskLaunchResult(
        task=launched,
        session=session,
        launch_guardrails={"passed": True, "reasons": [], "adapter_id": selected_adapter_id},
    )


def _apply_manual_estimate(
    database_path: Path | str, task: dict[str, Any], estimate_tokens: int | None, model: str
) -> dict[str, Any]:
    if estimate_tokens is None:
        return task
    return db.update_task(
        database_path,
        task["id"],
        {
            "status": "Estimated",
            "estimate_tokens": estimate_tokens,
            "recommended_model": model,
            "metadata": {**task.get("metadata", {}), "estimation_source": "manual"},
        },
    )


def _is_manual_estimate_required(task: dict[str, Any]) -> bool:
    metadata = task.get("metadata", {})
    return task.get("status") == "Blocked" and (
        metadata.get("requires_manual_estimate") is True
        or metadata.get("estimation_source") == "manual_required"
    )



def refresh_task_from_session(database_path: Path | str, task_id: str) -> dict[str, Any]:
    task = db.get_task(database_path, task_id)
    session_id = task.get("session_id")
    if not session_id:
        return task
    artifact = db.build_session_artifact(database_path, session_id)
    session_status = artifact["session"]["status"]
    metadata = dict(task.get("metadata", {}))
    metadata["session_finalized_status"] = session_status
    if session_status == "completed":
        has_issues = bool(artifact["alarms"]) or any(
            not checkpoint["passed"] for checkpoint in artifact["checkpoint_results"]
        )
        return db.update_task(
            database_path,
            task_id,
            {"status": "Review" if has_issues else "Done", "metadata": metadata},
        )
    if session_status in {"failed", "aborted"}:
        metadata.setdefault("blocked_reason", f"Session {session_status}.")
        return db.update_task(database_path, task_id, {"status": "Blocked", "metadata": metadata})
    return task


def _mark_launch_blocked(database_path: Path | str, task: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    has_estimate = task.get("estimate_tokens") is not None and bool(task.get("recommended_model"))
    status = "Estimated" if has_estimate else "Blocked"
    reason = reasons[0] if reasons else "Launch guardrails failed."
    metadata = {
        **task.get("metadata", {}),
        "launch_blocked_reason": reason,
        "launch_guardrail_reasons": list(reasons),
    }
    if status == "Blocked":
        metadata.setdefault("blocked_reason", reason)
    return db.update_task(database_path, task["id"], {"status": status, "metadata": metadata})


def _mark_launch_status_blocked(database_path: Path | str, task: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    reason = reasons[0] if reasons else "Launch is not allowed for this task status."
    return db.update_task(
        database_path,
        task["id"],
        {
            "metadata": {
                **task.get("metadata", {}),
                "launch_blocked_reason": reason,
                "launch_guardrail_reasons": list(reasons),
            }
        },
    )


def _default_adapter_id(database_path: Path | str) -> str | None:
    adapters = db.list_worker_adapters(database_path)
    for adapter in adapters:
        if adapter.get("is_default"):
            return str(adapter["id"])
    for adapter in adapters:
        if adapter.get("verification_status") == "verified":
            return str(adapter["id"])
    return adapters[0]["id"] if adapters else None


def _hash_key(session_api_key: str) -> str:
    return hashlib.sha256(session_api_key.encode("utf-8")).hexdigest()


def _result_field(result: Any, field: str, default: Any = "") -> Any:
    if isinstance(result, dict):
        return result.get(field, default)
    return getattr(result, field, default)


def _safe_text(value: str, *, limit: int = 500) -> str:
    safe = SESSION_KEY_PATTERN.sub("***REDACTED***", value)
    for pattern in SECRETISH_PATTERNS:
        safe = pattern.sub("***REDACTED***", safe)
    return safe[:limit]
