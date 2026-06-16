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
    _parse_native_usage_evidence,
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
    budget_override: bool = False,
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

    budget_check = _evaluate_launch_budget(database_path, task)
    if not budget_check["passed"] and not budget_override:
        blocked = _mark_budget_launch_blocked(database_path, task, budget_check)
        raise TaskLaunchBlocked(blocked, [budget_check["reason"]])

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

    metadata = task.get("metadata") or {}
    read_only = bool(metadata.get("read_only")) or metadata.get("launch_mode") == "read_only"
    write_capable = bool(metadata.get("write_capable")) or metadata.get("launch_mode") == "write_capable"
    tracking_mode = (guardrails.adapter.get("verification_evidence") or {}).get("tracking_mode") or "proxy_governed"
    usage_source = "native_usage" if tracking_mode == "native_usage" else "harness_proxy"
    project_root = metadata.get("project_root_path") if (read_only or write_capable) else None
    before_tree = _git_porcelain(project_root) if project_root else None
    task_branch = None
    if write_capable:
        cleanliness_reasons = _write_cleanliness_failures(project_root)
        if cleanliness_reasons:
            blocked = _mark_write_launch_blocked(database_path, task, cleanliness_reasons)
            raise TaskLaunchBlocked(blocked, cleanliness_reasons)

    session = db.create_session(
        database_path,
        task_description=task["description"],
        model=selected_model,
        session_key_hash=_hash_key(session_api_key),
        guardrail_overrides={
            "task_launch": {
                "task_id": task_id,
                "adapter_id": selected_adapter_id,
                "tracking_mode": tracking_mode,
                "usage_source": usage_source,
            },
            "budget": _session_budget_overrides(task, budget_check, budget_override),
        },
        status="running",
    )
    if write_capable:
        task_branch = _create_task_branch(project_root, task)

    builder = get_adapter_builder(guardrails.adapter)
    if tracking_mode == "native_usage":
        plan = builder.build_native_launch_command(
            model=selected_model,
            task_prompt=task["description"],
        )
    else:
        plan = builder.build_launch_command(
            model=selected_model,
            task_prompt=task["description"],
            proxy_url=selected_proxy_url,
            session_api_key=session_api_key,
        )
    plan = replace(
        plan,
        metadata={
            **plan.metadata,
            "session_id": session["id"],
            "task_id": task_id,
            "launch_mode": "write_capable" if write_capable else "read_only" if read_only else "standard",
            **({"task_branch": task_branch} if task_branch else {}),
        },
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
                "tracking_mode": tracking_mode,
                "usage_source": usage_source,
                "launch_command_plan": command_plan,
                "launch_mode": "write_capable" if write_capable else "read_only" if read_only else "standard",
                "budget_check": budget_check,
                **({"budget_override": {"approved": True, "reason": "operator_approved_launch"}} if budget_override else {}),
                **({"task_branch": task_branch} if task_branch else {}),
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
                    **({"diff_summary": _git_diff_summary(project_root)} if write_capable else {}),
                },
            },
        )
        raise TaskLaunchBlocked(failed, ["Worker adapter launch failed."])

    if tracking_mode == "native_usage":
        native_evidence = _parse_native_usage_evidence(stdout, model=selected_model)
        if native_evidence is None:
            reason = "No budget-authoritative native Worker usage evidence was emitted by the adapter."
            db.update_session_status(database_path, session["id"], "failed")
            failed = db.update_task(
                database_path,
                task_id,
                {
                    "status": "Blocked",
                    "session_id": session["id"],
                    "metadata": {
                        **claimed.get("metadata", {}),
                        "launch_blocked_reason": reason,
                        "launch_guardrail_reasons": [reason],
                        "launch_returncode": returncode,
                        "launch_stdout": _safe_text(stdout),
                        **({"diff_summary": _git_diff_summary(project_root)} if write_capable else {}),
                    },
                },
            )
            raise TaskLaunchBlocked(failed, [reason])
        db.record_token_turn(
            database_path,
            session_id=session["id"],
            usage_kind="task_execution",
            model=selected_model,
            prompt_tokens=native_evidence.prompt_tokens,
            completion_tokens=native_evidence.completion_tokens,
            cost=native_evidence.cost,
            raw_usage={**native_evidence.raw_usage, "usage_source": usage_source, "tracking_mode": tracking_mode},
        )

    if (read_only or write_capable) and not _session_has_worker_token_usage(database_path, session["id"]):
        reason = "No Worker model call was observed through the Harness Proxy."
        db.update_session_status(database_path, session["id"], "failed")
        failed = db.update_task(
            database_path,
            task_id,
            {
                "status": "Blocked",
                "session_id": session["id"],
                "metadata": {
                    **claimed.get("metadata", {}),
                    "launch_blocked_reason": reason,
                    "launch_guardrail_reasons": [reason],
                    "launch_returncode": returncode,
                    "launch_stdout": _safe_text(stdout),
                    **({"diff_summary": _git_diff_summary(project_root)} if write_capable else {}),
                },
            },
        )
        raise TaskLaunchBlocked(failed, [reason])

    if write_capable:
        write_result = _finalize_write_capable_launch(
            database_path=database_path,
            task_id=task_id,
            task=task,
            claimed=claimed,
            session=session,
            project_root=project_root,
            returncode=returncode,
            stdout=stdout,
        )
        return TaskLaunchResult(
            task=write_result,
            session=db.get_session(database_path, session["id"]),
            launch_guardrails={"passed": True, "reasons": [], "adapter_id": selected_adapter_id},
        )

    after_tree = _git_porcelain(project_root) if project_root else before_tree
    if read_only and before_tree != after_tree:
        db.update_session_status(database_path, session["id"], "failed")
        failed = db.update_task(
            database_path,
            task_id,
            {
                "status": "Blocked",
                "session_id": session["id"],
                "metadata": {
                    **claimed.get("metadata", {}),
                    "launch_blocked_reason": "Read-only Worker session modified the connected project.",
                    "launch_guardrail_reasons": ["Read-only Worker session modified the connected project."],
                    "readonly_diff_evidence": {"before": before_tree, "after": after_tree},
                    "launch_returncode": returncode,
                    "launch_stdout": _safe_text(stdout),
                },
            },
        )
        raise TaskLaunchBlocked(failed, ["Read-only Worker session modified the connected project."])

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
                **(_read_only_report_metadata(task) if read_only else {}),
            },
        },
    )
    _record_budget_overrun_if_needed(database_path, session["id"])
    if read_only:
        db.update_session_status(database_path, session["id"], "completed")
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


def _mark_write_launch_blocked(database_path: Path | str, task: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    reason = reasons[0] if reasons else "Write-capable launch guardrails failed."
    return db.update_task(
        database_path,
        task["id"],
        {
            "status": "Blocked",
            "metadata": {
                **task.get("metadata", {}),
                "launch_blocked_reason": reason,
                "launch_guardrail_reasons": list(reasons),
                "blocked_reason": reason,
            },
        },
    )


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




def abort_worker_session(database_path: Path | str, session_id: str, *, reason: str) -> dict[str, Any]:
    session = db.update_session_status(database_path, session_id, "aborted")
    affected_tasks = []
    for task in db.list_tasks(database_path):
        if task.get("session_id") != session_id:
            continue
        metadata = {**task.get("metadata", {}), "abort_reason": reason, "blocked_reason": f"Session aborted: {reason}"}
        affected_tasks.append(db.update_task(database_path, task["id"], {"status": "Blocked", "metadata": metadata}))
    return {"session": session, "tasks": affected_tasks}


def _evaluate_launch_budget(database_path: Path | str, task: dict[str, Any]) -> dict[str, Any]:
    budget = (task.get("metadata") or {}).get("budget") or {}
    daily_cap = _optional_int(budget.get("daily_cap_tokens"))
    daily_used = _optional_int(budget.get("daily_used_tokens")) or 0
    if daily_cap is None:
        return {"passed": True, "reason": None, "estimate_tokens": task.get("estimate_tokens"), "remaining_tokens": None}
    current_used = db.token_usage_breakdown(database_path)["by_category"]["worker_execution"]
    remaining = max(daily_cap - daily_used - current_used, 0)
    estimate = int(task.get("estimate_tokens") or 0)
    passed = estimate <= remaining
    return {
        "passed": passed,
        "reason": None if passed else "Task estimate exceeds remaining launch budget.",
        "estimate_tokens": estimate,
        "daily_cap_tokens": daily_cap,
        "daily_used_tokens": daily_used,
        "current_recorded_tokens": current_used,
        "remaining_tokens": remaining,
    }


def _mark_budget_launch_blocked(database_path: Path | str, task: dict[str, Any], budget_check: dict[str, Any]) -> dict[str, Any]:
    reason = budget_check.get("reason") or "Launch budget guardrail failed."
    status = "Estimated" if task.get("estimate_tokens") and task.get("recommended_model") else "Blocked"
    return db.update_task(
        database_path,
        task["id"],
        {
            "status": status,
            "metadata": {
                **task.get("metadata", {}),
                "launch_blocked_reason": reason,
                "launch_guardrail_reasons": [reason],
                "budget_check": budget_check,
                "budget_override_available": True,
            }
        },
    )


def _session_budget_overrides(task: dict[str, Any], budget_check: dict[str, Any], budget_override: bool) -> dict[str, Any]:
    budget = dict((task.get("metadata") or {}).get("budget") or {})
    budget["launch_budget_check"] = budget_check
    if budget_override:
        budget["budget_override"] = True
        budget["budget_override_reason"] = "operator_approved_launch"
    return budget


def _record_budget_overrun_if_needed(database_path: Path | str, session_id: str) -> None:
    session = db.get_session(database_path, session_id)
    budget = session.get("guardrail_overrides", {}).get("budget", {})
    session_cap = _optional_int(budget.get("session_cap_tokens"))
    daily_cap = _optional_int(budget.get("daily_cap_tokens"))
    daily_used = _optional_int(budget.get("daily_used_tokens")) or 0
    worker_breakdown = db.token_usage_breakdown(database_path)["by_category"]
    session_used = db.session_token_breakdown(database_path, session_id)["by_category"]["worker_execution"]
    daily_total = daily_used + worker_breakdown["worker_execution"]
    overrun = None
    if session_cap is not None and session_used > session_cap:
        overrun = {"scope": "session", "used_tokens": session_used, "cap_tokens": session_cap}
    elif daily_cap is not None and daily_total > daily_cap:
        overrun = {"scope": "daily", "used_tokens": daily_total, "cap_tokens": daily_cap}
    if overrun is None:
        return
    existing = db.list_alarms(database_path, session_id=session_id, alarm_type="BUDGET_OVERRUN")
    if existing:
        return
    db.record_alarm(
        database_path,
        session_id=session_id,
        alarm={
            "id": f"alarm_{secrets.token_hex(8)}",
            "type": "BUDGET_OVERRUN",
            "severity": "high",
            "context": overrun,
            "recommended_action": "Review budget overrun; session was not automatically killed.",
        },
    )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def detect_pr_capability(root_path: Path | str) -> dict[str, Any]:
    root = Path(root_path)
    remotes = _git_lines(root, ["remote", "-v"])
    github_remote = any("github.com" in line for line in remotes)
    if not github_remote:
        return {"available": False, "github_remote": False, "gh_authenticated": False, "reason": "GitHub remote is not configured."}
    gh_exists = subprocess.run(["which", "gh"], capture_output=True, text=True, check=False).returncode == 0
    if not gh_exists:
        return {"available": False, "github_remote": True, "gh_authenticated": False, "reason": "gh CLI is not installed."}
    auth = subprocess.run(["gh", "auth", "status"], cwd=str(root), capture_output=True, text=True, check=False, timeout=10)
    authenticated = auth.returncode == 0
    return {
        "available": authenticated,
        "github_remote": True,
        "gh_authenticated": authenticated,
        "reason": None if authenticated else "gh CLI is not authenticated.",
    }


def _write_cleanliness_failures(root_path: str | None) -> list[str]:
    if not root_path:
        return ["Connected project path is required for write-capable launch."]
    root = Path(root_path)
    if not (root / ".git").exists():
        return ["Write-capable launch requires a git repository."]
    branch = _current_branch(root)
    if not branch:
        return ["Write-capable launch requires a visible current git branch."]
    status = _git_porcelain(str(root))
    if status:
        return ["Write-capable launch requires a clean working tree before launch."]
    return []


def _create_task_branch(root_path: str | None, task: dict[str, Any]) -> str:
    root = Path(str(root_path))
    branch = f"htb/task-{task['id'].replace('task_', '')[:8]}-{_slug(task['description'])}"
    result = subprocess.run(["git", "checkout", "-b", branch], cwd=str(root), capture_output=True, text=True, check=False, timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"failed to create task branch: {_safe_text(result.stderr or result.stdout)}")
    return branch


def _finalize_write_capable_launch(
    *,
    database_path: Path | str,
    task_id: str,
    task: dict[str, Any],
    claimed: dict[str, Any],
    session: dict[str, Any],
    project_root: str | None,
    returncode: int,
    stdout: str,
) -> dict[str, Any]:
    profile = (task.get("metadata") or {}).get("project_profile") or {}
    test_command = profile.get("test_command")
    diff_summary = _git_diff_summary(project_root)
    _record_budget_overrun_if_needed(database_path, session["id"])
    base_metadata = {
        **claimed.get("metadata", {}),
        "launch_returncode": returncode,
        "launch_stdout": _safe_text(stdout),
        "diff_summary": diff_summary,
        "pr_capability": detect_pr_capability(project_root) if project_root else {"available": False, "reason": "No project root."},
    }
    if not test_command:
        db.update_session_status(database_path, session["id"], "completed")
        return db.update_task(
            database_path,
            task_id,
            {
                "status": "Review",
                "session_id": session["id"],
                "metadata": {
                    **base_metadata,
                    "post_run_verification": {"passed": False, "reason": "No test command configured."},
                    "manual_commit_approval_required": True,
                },
            },
        )

    verification = _run_test_command(project_root, str(test_command))
    if not verification["passed"]:
        db.update_session_status(database_path, session["id"], "failed")
        failed = db.update_task(
            database_path,
            task_id,
            {
                "status": "Blocked",
                "session_id": session["id"],
                "metadata": {
                    **base_metadata,
                    "post_run_verification": verification,
                    "launch_blocked_reason": "Post-run verification failed.",
                    "launch_guardrail_reasons": ["Post-run verification failed."],
                },
            },
        )
        raise TaskLaunchBlocked(failed, ["Post-run verification failed."])

    commit = _create_harness_commit(project_root, task, session) if diff_summary["has_changes"] else None
    db.update_session_status(database_path, session["id"], "completed")
    return db.update_task(
        database_path,
        task_id,
        {
            "status": "Review",
            "session_id": session["id"],
            "metadata": {
                **base_metadata,
                "post_run_verification": verification,
                **({"harness_commit": commit} if commit else {}),
            },
        },
    )


def _run_test_command(root_path: str | None, command: str) -> dict[str, Any]:
    result = subprocess.run(command, cwd=str(root_path), shell=True, capture_output=True, text=True, check=False, timeout=120)
    return {
        "command": command,
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": _safe_text(result.stdout, limit=1000),
        "stderr": _safe_text(result.stderr, limit=1000),
    }


def _git_diff_summary(root_path: str | None) -> dict[str, Any]:
    if not root_path:
        return {"has_changes": False, "files_changed": [], "stat": ""}
    root = Path(root_path)
    porcelain = _git_porcelain(str(root)) or ""
    files = []
    for line in porcelain.splitlines():
        if not line:
            continue
        files.append(line[3:] if len(line) > 3 else line)
    stat = subprocess.run(["git", "diff", "--stat"], cwd=str(root), capture_output=True, text=True, check=False, timeout=10).stdout.strip()
    if not stat and files:
        stat = "\n".join(files)
    return {"has_changes": bool(files), "files_changed": files, "stat": stat, "porcelain": porcelain}


def _create_harness_commit(root_path: str | None, task: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    root = Path(str(root_path))
    subprocess.run(["git", "add", "-A"], cwd=str(root), check=True, capture_output=True, timeout=10)
    message = f"harness: complete {task['id']}\n\nSession: {session['id']}\nTask: {task['description']}"
    subprocess.run(
        ["git", "-c", "user.email=harness@example.invalid", "-c", "user.name=AGILE-AI-HTB Harness", "commit", "-m", message],
        cwd=str(root),
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(root), check=True, capture_output=True, text=True, timeout=10).stdout.strip()
    return {"sha": sha, "message": message}


def _current_branch(root: Path) -> str | None:
    result = subprocess.run(["git", "branch", "--show-current"], cwd=str(root), capture_output=True, text=True, check=False, timeout=10)
    branch = result.stdout.strip()
    return branch or None


def _git_lines(root: Path, args: list[str]) -> list[str]:
    result = subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True, check=False, timeout=10)
    return result.stdout.splitlines()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (slug or "task")[:32]


def _session_has_worker_token_usage(database_path: Path | str, session_id: str) -> bool:
    artifact = db.build_session_artifact(database_path, session_id)
    return any(turn.get("usage_kind") == "task_execution" for turn in artifact["token_log"])


def _git_porcelain(root_path: str | None) -> str | None:
    if not root_path:
        return None
    root = Path(root_path)
    if not (root / ".git").exists():
        return ""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    return result.stdout.strip()


def _read_only_report_metadata(task: dict[str, Any]) -> dict[str, Any]:
    profile = (task.get("metadata") or {}).get("project_profile") or {}
    return {
        "session_report": {
            "language": profile.get("language_hints", []),
            "test_command": profile.get("test_command"),
            "run_command": profile.get("run_command"),
            "top_level_structure": profile.get("top_level_folders", []),
            "relevant_docs": profile.get("relevant_docs", []),
        }
    }


def _safe_text(value: str, *, limit: int = 500) -> str:
    safe = SESSION_KEY_PATTERN.sub("***REDACTED***", value)
    for pattern in SECRETISH_PATTERNS:
        safe = pattern.sub("***REDACTED***", safe)
    return safe[:limit]
