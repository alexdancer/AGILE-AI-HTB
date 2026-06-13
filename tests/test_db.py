import sqlite3

from agile_ai_htb.db import (
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
    update_session_status,
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
        token_turn_columns = {
            row["name"] for row in conn.execute("pragma table_info(token_turns)").fetchall()
        }

    assert {
        "sessions",
        "tasks",
        "token_turns",
        "tool_traces",
        "alarms",
        "guardrail_snapshots",
        "checkpoint_results",
        "action_history",
        "worker_adapters",
    }.issubset(tables)
    assert foreign_keys_enabled == 1
    assert "usage_kind" in token_turn_columns


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


def test_update_session_status_marks_final_state(tmp_path):
    db_path = tmp_path / "harness.db"
    init_db(db_path)
    session = create_session(
        db_path,
        task_description="Verify worker",
        model="claude-haiku",
        session_key_hash="hash-status",
        guardrail_overrides={},
    )

    updated = update_session_status(db_path, session["id"], "completed")

    assert updated["status"] == "completed"
    assert get_session(db_path, session["id"])["status"] == "completed"


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
        "usage_kind": "worker",
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
        "session_id": session["id"],
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


def test_record_token_turn_persists_explicit_usage_kind(tmp_path):
    db_path = tmp_path / "harness.db"
    init_db(db_path)
    session = create_session(
        db_path,
        task_description="Estimate task",
        model="gpt-4o-mini",
        session_key_hash="hash-estimator",
        guardrail_overrides={},
    )

    record_token_turn(
        db_path,
        session_id=session["id"],
        usage_kind="estimation",
        model="gpt-4o-mini",
        prompt_tokens=200,
        completion_tokens=50,
        cost=0.001,
        raw_usage={"prompt_tokens": 200, "completion_tokens": 50, "total_tokens": 250},
    )

    artifact = build_session_artifact(db_path, session["id"])

    assert artifact["token_log"][0]["usage_kind"] == "estimation"


def test_init_db_migrates_existing_token_turns_to_worker_usage_kind(tmp_path):
    db_path = tmp_path / "harness.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            create table sessions (
                id text primary key,
                task_description text not null,
                model text not null,
                session_key_hash text not null,
                started_at text not null,
                status text not null,
                guardrail_overrides_json text not null
            );
            create table token_turns (
                id integer primary key autoincrement,
                session_id text not null references sessions(id) on delete cascade,
                model text not null,
                prompt_tokens integer not null,
                completion_tokens integer not null,
                total_tokens integer not null,
                cost real not null,
                raw_usage_json text not null,
                created_at text not null
            );
            insert into sessions (
                id, task_description, model, session_key_hash, started_at, status,
                guardrail_overrides_json
            ) values (
                'sess_legacy', 'Legacy task', 'claude-haiku', 'legacy-hash',
                '2026-01-01T00:00:00+00:00', 'running', '{}'
            );
            insert into token_turns (
                session_id, model, prompt_tokens, completion_tokens, total_tokens,
                cost, raw_usage_json, created_at
            ) values (
                'sess_legacy', 'claude-haiku', 10, 5, 15, 0.01,
                '{"prompt_tokens":10,"completion_tokens":5,"total_tokens":15}',
                '2026-01-01T00:00:00+00:00'
            );
            """
        )

    init_db(db_path)

    artifact = build_session_artifact(db_path, "sess_legacy")
    with connect(db_path) as conn:
        token_turn_columns = {
            row["name"] for row in conn.execute("pragma table_info(token_turns)").fetchall()
        }

    assert "usage_kind" in token_turn_columns
    assert artifact["token_log"][0]["usage_kind"] == "worker"
