"""E2E smoke test: project → task → launch → Worker Run → token ledger → Review.

Uses synthetic data only — zero network, zero subprocess, zero real Worker CLI.
"""

from __future__ import annotations

from pathlib import Path

from foreman_ai_hq import db
from foreman_ai_hq.app import create_app
from foreman_ai_hq.settings import Settings
from foreman_ai_hq.task_launch import refresh_task_from_session

ROOT = Path(__file__).resolve().parents[2]
PORTAL_TOKEN = "test-portal-token"


def test_full_governance_loop_project_to_review(tmp_path, monkeypatch):
    """Prove the full governance loop works end-to-end:
    project connect → task create → Worker Run → token ledger → Review.
    """
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    database_path = tmp_path / "harness.db"
    settings = Settings(
        database_path=database_path,
        guardrails_path=ROOT / "guardrails.yaml",
    )
    db.init_db(settings.database_path)

    # 1. Connect a project
    project_root = tmp_path / "smoke-project"
    project_root.mkdir(exist_ok=True)
    project = db.upsert_connected_project(
        settings.database_path,
        name="smoke-project",
        root_path=str(project_root.resolve()),
        profile={
            "name": "smoke-project",
            "root_path": str(project_root.resolve()),
            "test_command": "pytest",
        },
        capability={"state": "launch_ready", "can_launch": True},
    )

    # 2. Mark a worker adapter as verified/launchable
    adapter = db.get_worker_adapter(settings.database_path, "opencode")
    db.update_worker_adapter(
        settings.database_path,
        adapter["id"],
        config={**adapter["config"], "tracking_mode": "native_usage"},
    )
    db.mark_worker_adapter_verification(
        settings.database_path,
        adapter["id"],
        verified=True,
        evidence={
            "mode": "native_usage",
            "passed": True,
            "model": "gpt-5.1-codex",
            "total_tokens": 42,
        },
    )

    # 3. Create a task
    task = db.create_task(
        settings.database_path,
        description="Smoke test: add hello world",
        status="Estimated",
        estimate_tokens=100,
        recommended_model="gpt-5.1-codex",
        metadata={"connected_project_id": project["id"], "project_root_path": str(project_root.resolve())},
    )

    # 4. Create a session (as launch would)
    session = db.create_session(
        settings.database_path,
        task_description=task["description"],
        model="gpt-5.1-codex",
        session_key_hash="smoke-session-hash",
        guardrail_overrides={},
    )

    # 5. Create a Worker Run (simulated launch)
    worker_run = db.create_worker_run(
        settings.database_path,
        task_id=task["id"],
        session_id=session["id"],
        adapter_id=adapter["id"],
        model="gpt-5.1-codex",
        tracking_mode="native_usage",
        command_plan={"command": ["smoke"], "redacted": True},
        metadata={"smoke_test": True},
    )

    # 6. Record synthetic token usage
    db.record_token_turn(
        settings.database_path,
        session_id=session["id"],
        usage_kind="task_execution",
        model="gpt-5.1-codex",
        prompt_tokens=50,
        completion_tokens=30,
        cost=0.0,
        raw_usage={"total_tokens": 80},
    )

    # 7. Mark Worker Run completed
    db.mark_worker_run_completed(
        settings.database_path,
        worker_run["id"],
        returncode=0,
        stdout="smoke test output",
        stderr="",
    )

    # 8. Mark session completed
    db.update_session_status(settings.database_path, session["id"], "completed")

    # 9. Link session to task
    db.update_task(settings.database_path, task["id"], {"session_id": session["id"], "actual_tokens": 80})

    # 10. Refresh task from session (mimics post-launch refresh)
    refresh_task_from_session(settings.database_path, task["id"])

    # 11. Verify
    updated_task = db.get_task(settings.database_path, task["id"])
    assert updated_task["status"] in {"Review", "Done"}, f"expected Review or Done, got {updated_task['status']}"

    # Verify Worker Run exists and completed
    runs = db.list_worker_runs(settings.database_path, task_id=task["id"])
    assert len(runs) == 1
    assert runs[0]["status"] == "completed"
    assert runs[0]["model"] == "gpt-5.1-codex"

    # Verify token turns recorded
    token_usage = db.session_token_usage(settings.database_path, session["id"])
    assert token_usage == 80, f"expected 80 tokens, got {token_usage}"

    # Verify task has actual tokens
    assert updated_task["actual_tokens"] == 80
