from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = """
create table if not exists sessions (
    id text primary key,
    task_description text not null,
    model text not null,
    session_key_hash text not null,
    started_at text not null,
    status text not null,
    guardrail_overrides_json text not null
);

create table if not exists tasks (
    id text primary key,
    description text not null,
    status text not null,
    estimate_tokens integer,
    recommended_model text,
    actual_tokens integer,
    session_id text references sessions(id) on delete set null,
    metadata_json text not null default '{}',
    created_at text not null
);

create table if not exists token_turns (
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

create table if not exists tool_traces (
    id integer primary key autoincrement,
    session_id text not null references sessions(id) on delete cascade,
    tool_name text not null,
    input_hash text not null,
    duration_ms integer,
    metadata_json text not null default '{}',
    created_at text not null
);

create table if not exists alarms (
    id text primary key,
    session_id text not null references sessions(id) on delete cascade,
    type text not null,
    severity text not null,
    context_json text not null,
    recommended_action text not null,
    resolved_at text,
    created_at text not null
);

create table if not exists guardrail_snapshots (
    id integer primary key autoincrement,
    session_id text not null references sessions(id) on delete cascade,
    zone text not null,
    decision_json text not null,
    created_at text not null
);

create table if not exists checkpoint_results (
    id integer primary key autoincrement,
    session_id text not null references sessions(id) on delete cascade,
    name text not null,
    passed integer not null,
    details_json text not null,
    created_at text not null
);

create table if not exists action_history (
    id integer primary key autoincrement,
    session_id text references sessions(id) on delete cascade,
    alarm_id text references alarms(id) on delete set null,
    action text not null,
    payload_json text not null default '{}',
    created_at text not null
);
"""


def connect(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma foreign_keys = on")
    return conn


def init_db(path: Path | str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)


def create_session(
    path: Path | str,
    *,
    task_description: str,
    model: str,
    session_key_hash: str,
    guardrail_overrides: dict[str, Any],
    status: str = "running",
) -> dict[str, Any]:
    session_id = f"sess_{uuid.uuid4().hex}"
    started_at = _now_iso()
    with connect(path) as conn:
        conn.execute(
            """
            insert into sessions (
                id, task_description, model, session_key_hash, started_at, status, guardrail_overrides_json
            ) values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                task_description,
                model,
                session_key_hash,
                started_at,
                status,
                _to_json(guardrail_overrides),
            ),
        )
    return get_session(path, session_id)


def get_session(path: Path | str, session_id: str) -> dict[str, Any]:
    with connect(path) as conn:
        row = conn.execute("select * from sessions where id = ?", (session_id,)).fetchone()
    if row is None:
        raise KeyError(f"session not found: {session_id}")
    return _session_from_row(row)


def record_token_turn(
    path: Path | str,
    *,
    session_id: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost: float,
    raw_usage: dict[str, Any],
) -> None:
    total_tokens = int(raw_usage.get("total_tokens", prompt_tokens + completion_tokens))
    with connect(path) as conn:
        conn.execute(
            """
            insert into token_turns (
                session_id, model, prompt_tokens, completion_tokens, total_tokens, cost, raw_usage_json, created_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                model,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                cost,
                _to_json(raw_usage),
                _now_iso(),
            ),
        )


def record_tool_trace(
    path: Path | str,
    *,
    session_id: str,
    tool_name: str,
    input_hash: str,
    duration_ms: int | None,
    metadata: dict[str, Any],
) -> None:
    with connect(path) as conn:
        conn.execute(
            """
            insert into tool_traces (session_id, tool_name, input_hash, duration_ms, metadata_json, created_at)
            values (?, ?, ?, ?, ?, ?)
            """,
            (session_id, tool_name, input_hash, duration_ms, _to_json(metadata), _now_iso()),
        )


def record_guardrail_snapshot(
    path: Path | str,
    *,
    session_id: str,
    zone: str,
    decision: dict[str, Any],
) -> None:
    with connect(path) as conn:
        conn.execute(
            """
            insert into guardrail_snapshots (session_id, zone, decision_json, created_at)
            values (?, ?, ?, ?)
            """,
            (session_id, zone, _to_json(decision), _now_iso()),
        )


def record_alarm(path: Path | str, *, session_id: str, alarm: dict[str, Any]) -> None:
    with connect(path) as conn:
        conn.execute(
            """
            insert into alarms (id, session_id, type, severity, context_json, recommended_action, created_at)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alarm["id"],
                session_id,
                alarm["type"],
                alarm["severity"],
                _to_json(alarm.get("context", {})),
                alarm["recommended_action"],
                _now_iso(),
            ),
        )


def record_checkpoint_result(
    path: Path | str,
    *,
    session_id: str,
    checkpoint: dict[str, Any],
) -> None:
    with connect(path) as conn:
        conn.execute(
            """
            insert into checkpoint_results (session_id, name, passed, details_json, created_at)
            values (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                checkpoint["name"],
                1 if checkpoint["passed"] else 0,
                _to_json(checkpoint.get("details", {})),
                _now_iso(),
            ),
        )


def build_session_artifact(path: Path | str, session_id: str) -> dict[str, Any]:
    with connect(path) as conn:
        session_row = conn.execute("select * from sessions where id = ?", (session_id,)).fetchone()
        if session_row is None:
            raise KeyError(f"session not found: {session_id}")
        token_rows = conn.execute(
            "select * from token_turns where session_id = ? order by id", (session_id,)
        ).fetchall()
        tool_trace_rows = conn.execute(
            "select * from tool_traces where session_id = ? order by id", (session_id,)
        ).fetchall()
        snapshot_rows = conn.execute(
            "select * from guardrail_snapshots where session_id = ? order by id", (session_id,)
        ).fetchall()
        alarm_rows = conn.execute(
            "select * from alarms where session_id = ? order by created_at, id", (session_id,)
        ).fetchall()
        checkpoint_rows = conn.execute(
            "select * from checkpoint_results where session_id = ? order by id", (session_id,)
        ).fetchall()

    return {
        "session": _session_from_row(session_row),
        "token_log": [_token_turn_from_row(row) for row in token_rows],
        "tool_trace": [_tool_trace_from_row(row) for row in tool_trace_rows],
        "alarms": [_alarm_from_row(row) for row in alarm_rows],
        "guardrail_snapshots": [_snapshot_from_row(row) for row in snapshot_rows],
        "checkpoint_results": [_checkpoint_from_row(row) for row in checkpoint_rows],
    }


def _session_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "task_description": row["task_description"],
        "model": row["model"],
        "session_key_hash": row["session_key_hash"],
        "started_at": row["started_at"],
        "status": row["status"],
        "guardrail_overrides": _from_json(row["guardrail_overrides_json"]),
    }


def _token_turn_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "model": row["model"],
        "prompt_tokens": row["prompt_tokens"],
        "completion_tokens": row["completion_tokens"],
        "total_tokens": row["total_tokens"],
        "cost": row["cost"],
        "raw_usage": _from_json(row["raw_usage_json"]),
        "created_at": row["created_at"],
    }


def _tool_trace_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "tool_name": row["tool_name"],
        "input_hash": row["input_hash"],
        "duration_ms": row["duration_ms"],
        "metadata": _from_json(row["metadata_json"]),
        "created_at": row["created_at"],
    }


def _snapshot_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "zone": row["zone"],
        "decision": _from_json(row["decision_json"]),
        "created_at": row["created_at"],
    }


def _alarm_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "type": row["type"],
        "severity": row["severity"],
        "context": _from_json(row["context_json"]),
        "recommended_action": row["recommended_action"],
        "created_at": row["created_at"],
        "resolved_at": row["resolved_at"],
    }


def _checkpoint_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "name": row["name"],
        "passed": bool(row["passed"]),
        "details": _from_json(row["details_json"]),
        "created_at": row["created_at"],
    }


def _to_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _from_json(value: str) -> dict[str, Any]:
    return json.loads(value)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
