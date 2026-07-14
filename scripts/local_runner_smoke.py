from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from foreman_ai_hq import db
from foreman_ai_hq.execution_backend import LocalExecutionBackend
from foreman_ai_hq.task_launch import TaskLaunchBlocked, launch_task
from foreman_ai_hq.worker_adapters import detect_worker_adapter


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _plan_value(plan: Any, key: str) -> Any:
    if isinstance(plan, dict):
        return plan.get(key) or (plan.get("metadata") or {}).get(key)
    value = getattr(plan, key, None)
    if value is not None:
        return value
    return (getattr(plan, "metadata", {}) or {}).get(key)


def _record_worker_tokens(database_path: Path, plan: Any) -> dict[str, Any]:
    db.record_token_turn(
        database_path,
        session_id=_plan_value(plan, "session_id"),
        usage_kind="task_execution",
        model=_plan_value(plan, "model") or "smoke-model",
        prompt_tokens=17,
        completion_tokens=5,
        cost=0.0,
        raw_usage={"total_tokens": 22, "endpoint": "/v1/chat/completions"},
    )
    return {"returncode": 0, "stdout": "smoke runner recorded token usage", "stderr": ""}


def _edit_docs_and_record_tokens(database_path: Path, repo: Path):
    def runner(plan: Any) -> dict[str, Any]:
        (repo / "SMOKE.md").write_text("# Local runner smoke proof\n", encoding="utf-8")
        db.record_token_turn(
            database_path,
            session_id=_plan_value(plan, "session_id"),
            usage_kind="task_execution",
            model=_plan_value(plan, "model") or "smoke-model",
            prompt_tokens=29,
            completion_tokens=11,
            cost=0.0,
            raw_usage={"total_tokens": 40, "endpoint": "/v1/chat/completions"},
        )
        return {"returncode": 0, "stdout": "edited SMOKE.md", "stderr": ""}

    return runner


def run_smoke(require_opencode: bool = True) -> int:
    with tempfile.TemporaryDirectory(prefix="foreman-ai-hq-local-smoke-") as tmp:
        root = Path(tmp)
        repo = root / "repo"
        repo.mkdir()
        _run(["git", "init"], repo)
        _run(["git", "config", "user.email", "smoke@example.invalid"], repo)
        _run(["git", "config", "user.name", "Foreman AI HQ Smoke"], repo)
        (repo / "README.md").write_text("# DEMO local runner smoke\n", encoding="utf-8")
        _run(["git", "add", "README.md"], repo)
        _run(["git", "commit", "-m", "seed smoke repo"], repo)

        database_path = root / "harness.db"
        db.init_db(database_path)
        backend = LocalExecutionBackend(database_path)
        connection = backend.connect_project(repo)
        if connection.error or connection.project is None:
            print(f"FAIL: project connection failed: {connection.error}")
            return 1
        project = connection.project
        capability = backend.project_capability(project)
        adapter = db.get_worker_adapter(database_path, "opencode") or {}
        opencode = detect_worker_adapter(adapter)
        if require_opencode and not opencode.get("installed"):
            print("SKIP: opencode is not installed; Local Runner project connection succeeded.")
            return 77
        smoke_model = (adapter.get("supported_models") or ["opencode/gpt-5.1"])[0]
        db.mark_worker_adapter_verification(
            database_path,
            "opencode",
            verified=True,
            evidence={
                "smoke": "synthetic-local-runner",
                "executable": opencode.get("executable"),
                "version": opencode.get("version"),
                "sentinel": "FOREMAN_AI_HQ_ADAPTER_OK",
            },
        )

        read_only = backend.create_read_only_proof_task(project)
        launch_task(
            database_path,
            read_only["id"],
            adapter_id="opencode",
            model=read_only.get("recommended_model"),
            proxy_url="http://127.0.0.1:8000/v1",
            runner=lambda plan: _record_worker_tokens(database_path, plan),
        )

        write_task = db.create_task(
            database_path,
            description="Create a docs-only smoke proof file.",
            status="Estimated",
            estimate_tokens=20,
            recommended_model=smoke_model,
            metadata={
                "title": "DEMO write smoke",
                "adapter_id": "opencode",
                "adapter_verified": True,
                "launch_mode": "write_capable",
                "project_root_path": str(repo),
                "project_profile": {"test_command": "python -c 'print(\"ok\")'"},
                "budget": {"daily_used_tokens": 95, "daily_cap_tokens": 100, "session_cap_tokens": 5},
            },
        )
        try:
            launch_task(
                database_path,
                write_task["id"],
                adapter_id="opencode",
                model=smoke_model,
                proxy_url="http://127.0.0.1:8000/v1",
                budget_override=True,
                runner=_edit_docs_and_record_tokens(database_path, repo),
            )
        except TaskLaunchBlocked as exc:
            print(f"FAIL: write smoke blocked: {exc.task.get('metadata', {}).get('launch_blocked_reason')}")
            return 1

        updated = db.get_task(database_path, write_task["id"])
        sessions = db.list_sessions(database_path)
        alarms = db.list_alarms(database_path)
        if updated["status"] != "Review":
            print(f"FAIL: expected write smoke task in Review, got {updated['status']}")
            return 1
        if not updated.get("session_id"):
            print("FAIL: write smoke task has no session_id")
            return 1
        print(
            "OK: local runner smoke passed "
            f"repo={repo} sessions={len(sessions)} alarms={len(alarms)} "
            f"branch={updated['metadata'].get('task_branch')} commit={updated['metadata'].get('harness_commit')}"
        )
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a synthetic Local Runner smoke test.")
    parser.add_argument(
        "--allow-missing-opencode",
        action="store_true",
        help="Return success instead of skip when opencode is not installed.",
    )
    args = parser.parse_args(argv)
    result = run_smoke(require_opencode=not args.allow_missing_opencode)
    if result == 77 and args.allow_missing_opencode:
        return 0
    return result


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
