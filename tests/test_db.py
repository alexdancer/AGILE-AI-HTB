import sqlite3

from token_tracker_harness.db import (
    build_session_artifact,
    connect,
    create_session,
    get_session,
    init_db,
    record_alarm,
    record_checkpoint_result,
    record_guardrail_snapshot,
    record_token_turn,
    record_tool_trace,
)


def test_init_db_creates_schema_idempotently_with_foreign_keys(tmp_path):
    db_path = tmp_path / "harness.db"

    init_db(db_path)
    init_db(db_path)

    with connect(db_path) as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "select name from sqlite_master where type = 'table' and name not like 'sqlite_%'"
            )
        }
        foreign_keys_enabled = conn.execute("pragma foreign_keys").fetchone()[0]

    assert {
        "sessions",
        "tasks",
        "token_turns",
        "tool_traces",
        "alarms",
        "guardrail_snapshots",
        "checkpoint_results",
        "action_history",
    }.issubset(tables)
    assert foreign_keys_enabled == 1


def test_create_and_get_session_round_trips_json_overrides(tmp_path):
    db_path = tmp_path / "harness.db"
    init_db(db_path)

    session = create_session(
        db_path,
        task_description="Implement snip save",
        model="claude-haiku",
        session_key_hash="hash-123",
        guardrail_overrides={"session_cap": {"tokens": 50_000}},
    )

    loaded = get_session(db_path, session["id"])

    assert loaded == session
    assert loaded["status"] == "running"
    assert loaded["task_description"] == "Implement snip save"
    assert loaded["model"] == "claude-haiku"
    assert loaded["session_key_hash"] == "hash-123"
    assert loaded["guardrail_overrides"] == {"session_cap": {"tokens": 50_000}}
    assert loaded["started_at"]


def test_session_artifact_rebuilds_persisted_session_rows(tmp_path):
    db_path = tmp_path / "harness.db"
    init_db(db_path)
    session = create_session(
        db_path,
        task_description="Implement snip list",
        model="claude-sonnet",
        session_key_hash="hash-456",
        guardrail_overrides={},
    )

    record_token_turn(
        db_path,
        session_id=session["id"],
        model="claude-sonnet",
        prompt_tokens=1200,
        completion_tokens=300,
        cost=0.0123,
        raw_usage={"prompt_tokens": 1200, "completion_tokens": 300, "total_tokens": 1600},
    )
    record_tool_trace(
        db_path,
        session_id=session["id"],
        tool_name="read_file",
        input_hash="hash-readme",
        duration_ms=42,
        metadata={"path": "README.md"},
    )
    record_guardrail_snapshot(
        db_path,
        session_id=session["id"],
        zone="yellow",
        decision={"max_tokens": 2048, "blocked_tools": ["web_search"]},
    )
    record_alarm(
        db_path,
        session_id=session["id"],
        alarm={
            "id": "alarm-1",
            "type": "BUDGET_YELLOW",
            "severity": "LOW",
            "context": {"zone": "yellow"},
            "recommended_action": "Agent constrained; no user action needed.",
        },
    )
    record_checkpoint_result(
        db_path,
        session_id=session["id"],
        checkpoint={
            "name": "budget_health",
            "passed": True,
            "details": {"spent": 1600},
        },
    )

    artifact = build_session_artifact(db_path, session["id"])

    assert artifact["session"]["id"] == session["id"]
    assert artifact["session"]["task_description"] == "Implement snip list"
    token_turn = artifact["token_log"][0]
    assert token_turn == {
        "model": "claude-sonnet",
        "prompt_tokens": 1200,
        "completion_tokens": 300,
        "total_tokens": 1600,
        "cost": 0.0123,
        "raw_usage": {"prompt_tokens": 1200, "completion_tokens": 300, "total_tokens": 1600},
        "created_at": token_turn["created_at"],
    }
    assert token_turn["created_at"]
    tool_trace = artifact["tool_trace"][0]
    assert tool_trace == {
        "tool_name": "read_file",
        "input_hash": "hash-readme",
        "duration_ms": 42,
        "metadata": {"path": "README.md"},
        "created_at": tool_trace["created_at"],
    }
    assert tool_trace["created_at"]
    snapshot = artifact["guardrail_snapshots"][0]
    assert snapshot == {
        "zone": "yellow",
        "decision": {"max_tokens": 2048, "blocked_tools": ["web_search"]},
        "created_at": snapshot["created_at"],
    }
    alarm = artifact["alarms"][0]
    assert alarm == {
        "id": "alarm-1",
        "type": "BUDGET_YELLOW",
        "severity": "LOW",
        "context": {"zone": "yellow"},
        "recommended_action": "Agent constrained; no user action needed.",
        "created_at": alarm["created_at"],
        "resolved_at": None,
    }
    checkpoint = artifact["checkpoint_results"][0]
    assert checkpoint == {
        "name": "budget_health",
        "passed": True,
        "details": {"spent": 1600},
        "created_at": checkpoint["created_at"],
    }


def test_foreign_keys_reject_rows_for_unknown_session(tmp_path):
    db_path = tmp_path / "harness.db"
    init_db(db_path)

    try:
        record_token_turn(
            db_path,
            session_id="missing",
            model="claude-haiku",
            prompt_tokens=1,
            completion_tokens=2,
            cost=0.0,
            raw_usage={},
        )
    except sqlite3.IntegrityError:
        return

    raise AssertionError("expected sqlite3.IntegrityError for unknown session")
