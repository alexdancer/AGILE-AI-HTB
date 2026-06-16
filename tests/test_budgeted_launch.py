from __future__ import annotations

import json
from pathlib import Path

from agile_ai_htb import db
from agile_ai_htb.task_launch import TaskLaunchBlocked, abort_worker_session, launch_task


def _verified_budget_task(db_path: Path, tmp_path: Path, *, estimate: int = 50, budget: dict | None = None):
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(tmp_path),
        config={"launch_template": ["python", "-c", "print('worker')"]},
        supported_models=["opencode/gpt-5.1"],
        is_default=True,
    )
    db.mark_worker_adapter_verification(db_path, "opencode", verified=True, evidence={"ok": True})
    return db.create_task(
        db_path,
        description="Budgeted launch",
        status="Ready",
        estimate_tokens=estimate,
        recommended_model="opencode/gpt-5.1",
        metadata={"budget": budget or {"daily_used_tokens": 0, "daily_cap_tokens": 100, "session_cap_tokens": 100}},
    )


def _runner_recording(db_path: Path, *, total_tokens: int = 10):
    def runner(plan):
        db.record_token_turn(
            db_path,
            session_id=plan.metadata["session_id"],
            usage_kind="task_execution",
            model="opencode/gpt-5.1",
            prompt_tokens=total_tokens,
            completion_tokens=0,
            cost=0,
            raw_usage={"total_tokens": total_tokens},
        )
        return {"returncode": 0, "stdout": "done", "stderr": ""}

    return runner


def test_estimate_within_budget_launches(tmp_path):
    db_path = tmp_path / "harness.db"
    task = _verified_budget_task(db_path, tmp_path, estimate=50, budget={"daily_used_tokens": 25, "daily_cap_tokens": 100})

    result = launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=_runner_recording(db_path))

    assert result.task["status"] == "Running"
    assert result.task["metadata"]["budget_check"]["passed"] is True


def test_native_usage_launch_passes_selected_model_and_records_usage_metadata(tmp_path):
    db_path = tmp_path / "harness.db"
    task = _verified_budget_task(db_path, tmp_path, estimate=50, budget={"daily_used_tokens": 0, "daily_cap_tokens": 100})
    db.update_worker_adapter(
        db_path,
        "opencode",
        config={"command": "opencode"},
        supported_models=["opencode/gpt-5.1"],
    )
    db.mark_worker_adapter_verification(
        db_path,
        "opencode",
        verified=True,
        evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
    )
    calls = []

    def runner(plan):
        calls.append(plan)
        return {
            "returncode": 0,
            "stdout": json.dumps(
                {
                    "type": "complete",
                    "message": "HTB_SENTINEL_OK",
                    "model": "opencode/gpt-5.1",
                    "session_id": "opencode-session-2099",
                    "usage": {"input_tokens": 12, "output_tokens": 3, "total_tokens": 15, "cost": 0.01},
                }
            ),
            "stderr": "",
        }

    result = launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=runner)
    session = db.get_session(db_path, result.session["id"])
    with db.connect(db_path) as conn:
        token_turn = conn.execute("select * from token_turns where session_id = ?", (session["id"],)).fetchone()

    assert calls[0].command == ["opencode", "run", "--model", "opencode/gpt-5.1", "--format", "json", "Budgeted launch"]
    assert token_turn is not None
    assert calls[0].env == {}
    assert result.task["metadata"]["tracking_mode"] == "native_usage"
    assert result.task["metadata"]["usage_source"] == "native_usage"
    assert session["guardrail_overrides"]["task_launch"]["tracking_mode"] == "native_usage"
    assert token_turn["usage_kind"] == "task_execution"
    assert token_turn["total_tokens"] == 15
    assert json.loads(token_turn["raw_usage_json"])["usage_source"] == "native_usage"


def test_native_usage_launch_blocks_when_adapter_emits_no_usage_evidence(tmp_path):
    db_path = tmp_path / "harness.db"
    task = _verified_budget_task(db_path, tmp_path, estimate=50, budget={"daily_used_tokens": 0, "daily_cap_tokens": 100})
    db.update_worker_adapter(db_path, "opencode", config={"command": "opencode"}, supported_models=["opencode/gpt-5.1"])
    db.mark_worker_adapter_verification(
        db_path,
        "opencode",
        verified=True,
        evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
    )

    try:
        launch_task(
            db_path,
            task["id"],
            adapter_id="opencode",
            model=None,
            proxy_url=None,
            runner=lambda plan: {"returncode": 0, "stdout": "HTB_SENTINEL_OK", "stderr": ""},
        )
    except TaskLaunchBlocked as exc:
        blocked = exc.task
    else:
        raise AssertionError("expected native usage evidence block")

    assert blocked["status"] == "Blocked"
    assert blocked["metadata"]["launch_blocked_reason"] == "No budget-authoritative native Worker usage evidence was emitted by the adapter."


def test_token_usage_breakdown_classifies_control_worker_verification_and_reporting(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    session = db.create_session(
        db_path,
        task_description="ledger",
        model="control-plane",
        session_key_hash="b" * 64,
        guardrail_overrides={},
        status="completed",
    )
    rows = [
        ("estimation", "control", 10),
        ("task_execution", "worker", 20),
        ("adapter_verification", "worker", 5),
        ("reporting", "control", 3),
    ]
    for usage_kind, model, tokens in rows:
        db.record_token_turn(
            db_path,
            session_id=session["id"],
            usage_kind=usage_kind,
            model=model,
            prompt_tokens=tokens,
            completion_tokens=0,
            cost=0,
            raw_usage={"total_tokens": tokens},
        )

    breakdown = db.token_usage_breakdown(db_path)
    session_breakdown = db.session_token_breakdown(db_path, session["id"])

    assert breakdown["total_tokens"] == 38
    assert breakdown["by_category"] == {
        "control_plane": 10,
        "worker_execution": 20,
        "adapter_verification": 5,
        "reporting_summary": 3,
        "other": 0,
    }
    assert breakdown == session_breakdown
    assert breakdown["by_source"]["control_plane"] == 10
    assert breakdown["by_source"]["harness_proxy"] == 25


def test_worker_budget_overrun_ignores_control_plane_spend(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    control_session = db.create_session(
        db_path,
        task_description="control spend",
        model="control-plane",
        session_key_hash="c" * 64,
        guardrail_overrides={},
        status="completed",
    )
    db.record_token_turn(
        db_path,
        session_id=control_session["id"],
        usage_kind="estimation",
        model="control-plane",
        prompt_tokens=1000,
        completion_tokens=0,
        cost=0,
        raw_usage={"total_tokens": 1000},
    )
    task = _verified_budget_task(
        db_path,
        tmp_path,
        estimate=10,
        budget={"daily_used_tokens": 0, "daily_cap_tokens": 20, "session_cap_tokens": 20},
    )

    result = launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=_runner_recording(db_path, total_tokens=10))

    assert result.task["status"] == "Running"
    assert result.session is not None
    assert db.list_alarms(db_path, session_id=result.session["id"], alarm_type="BUDGET_OVERRUN") == []


def test_estimate_over_budget_blocks_without_runner_and_shows_override(tmp_path):
    db_path = tmp_path / "harness.db"
    task = _verified_budget_task(db_path, tmp_path, estimate=80, budget={"daily_used_tokens": 40, "daily_cap_tokens": 100})
    calls = []

    try:
        launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=lambda plan: calls.append(plan))
    except TaskLaunchBlocked as exc:
        blocked = exc.task
    else:
        raise AssertionError("expected budget block")

    assert blocked["status"] == "Estimated"
    assert blocked["metadata"]["budget_check"]["passed"] is False
    assert blocked["metadata"]["budget_override_available"] is True
    assert calls == []


def test_budget_override_is_recorded_and_audited_on_session(tmp_path):
    db_path = tmp_path / "harness.db"
    task = _verified_budget_task(db_path, tmp_path, estimate=80, budget={"daily_used_tokens": 40, "daily_cap_tokens": 100})

    result = launch_task(
        db_path,
        task["id"],
        adapter_id="opencode",
        model=None,
        proxy_url=None,
        budget_override=True,
        runner=_runner_recording(db_path),
    )
    session = db.get_session(db_path, result.session["id"])

    assert result.task["metadata"]["budget_override"]["approved"] is True
    assert session["guardrail_overrides"]["budget"]["budget_override"] is True
    assert session["guardrail_overrides"]["budget"]["budget_override_reason"] == "operator_approved_launch"


def test_budget_overrun_records_alarm_without_auto_killing_session(tmp_path):
    db_path = tmp_path / "harness.db"
    task = _verified_budget_task(db_path, tmp_path, estimate=10, budget={"daily_used_tokens": 0, "daily_cap_tokens": 100, "session_cap_tokens": 20})

    result = launch_task(db_path, task["id"], adapter_id="opencode", model=None, proxy_url=None, runner=_runner_recording(db_path, total_tokens=25))
    session = db.get_session(db_path, result.session["id"])
    alarms = db.list_alarms(db_path, session_id=session["id"])

    assert session["status"] == "running"
    assert result.task["status"] == "Running"
    assert alarms
    assert alarms[0]["type"] == "BUDGET_OVERRUN"


def test_manual_abort_preserves_task_metadata_and_marks_session_aborted(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    session = db.create_session(
        db_path,
        task_description="Abort me",
        model="opencode/gpt-5.1",
        session_key_hash="a" * 64,
        guardrail_overrides={"task_launch": {"task_branch": "htb/task-demo-2099"}},
        status="running",
    )
    task = db.create_task(
        db_path,
        description="Abort me",
        status="Running",
        estimate_tokens=10,
        recommended_model="opencode/gpt-5.1",
        session_id=session["id"],
        metadata={"task_branch": "htb/task-demo-2099", "diff_summary": {"files_changed": ["demo.py"]}},
    )
    db.record_token_turn(
        db_path,
        session_id=session["id"],
        usage_kind="task_execution",
        model="opencode/gpt-5.1",
        prompt_tokens=1,
        completion_tokens=1,
        cost=0,
        raw_usage={"total_tokens": 2},
    )

    aborted = abort_worker_session(db_path, session["id"], reason="operator stopped runaway task")
    refreshed = db.get_task(db_path, task["id"])
    artifact = db.build_session_artifact(db_path, session["id"])

    assert aborted["session"]["status"] == "aborted"
    assert refreshed["status"] == "Blocked"
    assert refreshed["metadata"]["abort_reason"] == "operator stopped runaway task"
    assert refreshed["metadata"]["task_branch"] == "htb/task-demo-2099"
    assert artifact["token_log"][0]["total_tokens"] == 2
