from __future__ import annotations

import json
import re
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
    usage_kind text not null default 'worker',
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

create table if not exists worker_adapters (
    id text primary key,
    kind text not null,
    name text not null,
    workdir text,
    config_json text not null default '{}',
    supported_models_json text not null default '[]',
    is_default integer not null default 0,
    verification_status text not null default 'unverified',
    verification_evidence_json text not null default '{}',
    verified_at text,
    created_at text not null,
    updated_at text not null
);
"""

WORKER_ADAPTER_PRESETS = [
    {
        "id": "claude_code",
        "kind": "claude_code",
        "name": "Claude Code",
        "config": {"verification_template": ["claude", "-p", "{prompt}"], "launch_template": ["claude"]},
        "supported_models": ["claude-3-5-sonnet-latest", "claude-3-5-sonnet-20240620", "claude-3-haiku-20240307"],
    },
    {
        "id": "codex",
        "kind": "codex",
        "name": "Codex",
        "config": {"verification_template": ["codex", "--prompt", "{prompt}"], "launch_template": ["codex"]},
        "supported_models": ["gpt-5.1-codex", "openai/gpt-4.1-mini"],
    },
    {
        "id": "opencode",
        "kind": "opencode",
        "name": "OpenCode",
        "config": {"verification_template": ["opencode", "run", "{prompt}"], "launch_template": ["opencode"]},
        "supported_models": ["opencode/gpt-5.1", "gpt-5.1-codex"],
    },
]


def connect(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma foreign_keys = on")
    return conn


def init_db(path: Path | str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        _migrate_schema(conn)
        _seed_worker_adapters(conn)


def _migrate_schema(conn: sqlite3.Connection) -> None:
    token_turn_columns = {
        row["name"] for row in conn.execute("pragma table_info(token_turns)").fetchall()
    }
    if "usage_kind" not in token_turn_columns:
        conn.execute("alter table token_turns add column usage_kind text not null default 'worker'")

    worker_adapter_tables = {
        row["name"]
        for row in conn.execute(
            "select name from sqlite_master where type = 'table' and name = 'worker_adapters'"
        ).fetchall()
    }
    if "worker_adapters" not in worker_adapter_tables:
        conn.execute(
            """
            create table worker_adapters (
                id text primary key,
                kind text not null,
                name text not null,
                workdir text,
                config_json text not null default '{}',
                supported_models_json text not null default '[]',
                is_default integer not null default 0,
                verification_status text not null default 'unverified',
                verification_evidence_json text not null default '{}',
                verified_at text,
                created_at text not null,
                updated_at text not null
            )
            """
        )


def _seed_worker_adapters(conn: sqlite3.Connection) -> None:
    now = _now_iso()
    for preset in WORKER_ADAPTER_PRESETS:
        conn.execute(
            """
            insert into worker_adapters (
                id, kind, name, config_json, supported_models_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do update set
                kind = excluded.kind,
                name = excluded.name
            """,
            (
                preset["id"],
                preset["kind"],
                preset["name"],
                _to_json(preset["config"]),
                json.dumps(preset["supported_models"], sort_keys=True, separators=(",", ":")),
                now,
                now,
            ),
        )


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


def get_session_by_key_hash(path: Path | str, session_key_hash: str) -> dict[str, Any]:
    with connect(path) as conn:
        row = conn.execute(
            "select * from sessions where session_key_hash = ?", (session_key_hash,)
        ).fetchone()
    if row is None:
        raise KeyError("session not found for key")
    return _session_from_row(row)


def update_session_status(path: Path | str, session_id: str, status: str) -> dict[str, Any]:
    with connect(path) as conn:
        cursor = conn.execute("update sessions set status = ? where id = ?", (status, session_id))
        if cursor.rowcount == 0:
            raise KeyError(f"session not found: {session_id}")
    return get_session(path, session_id)


def record_token_turn(
    path: Path | str,
    *,
    session_id: str,
    usage_kind: str = "worker",
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
                session_id, usage_kind, model, prompt_tokens, completion_tokens,
                total_tokens, cost, raw_usage_json, created_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                usage_kind,
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


def create_task(
    path: Path | str,
    *,
    description: str,
    status: str = "Blocked",
    estimate_tokens: int | None = None,
    recommended_model: str | None = None,
    actual_tokens: int | None = None,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task_id = f"task_{uuid.uuid4().hex}"
    with connect(path) as conn:
        conn.execute(
            """
            insert into tasks (
                id, description, status, estimate_tokens, recommended_model,
                actual_tokens, session_id, metadata_json, created_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                description,
                status,
                estimate_tokens,
                recommended_model,
                actual_tokens,
                session_id,
                _to_json(metadata or {}),
                _now_iso(),
            ),
        )
    return get_task(path, task_id)


def get_task(path: Path | str, task_id: str) -> dict[str, Any]:
    with connect(path) as conn:
        row = conn.execute("select * from tasks where id = ?", (task_id,)).fetchone()
    if row is None:
        raise KeyError(f"task not found: {task_id}")
    return _task_from_row(row)


def update_task(path: Path | str, task_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "description": "description",
        "status": "status",
        "estimate_tokens": "estimate_tokens",
        "recommended_model": "recommended_model",
        "actual_tokens": "actual_tokens",
        "session_id": "session_id",
        "metadata": "metadata_json",
    }
    assignments: list[str] = []
    values: list[Any] = []
    for key, value in updates.items():
        if key not in allowed or value is None:
            continue
        assignments.append(f"{allowed[key]} = ?")
        values.append(_to_json(value) if key == "metadata" else value)
    if not assignments:
        return get_task(path, task_id)

    with connect(path) as conn:
        cursor = conn.execute(
            f"update tasks set {', '.join(assignments)} where id = ?",
            (*values, task_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(f"task not found: {task_id}")
    return get_task(path, task_id)


def list_tasks(path: Path | str) -> list[dict[str, Any]]:
    with connect(path) as conn:
        rows = conn.execute("select * from tasks order by created_at, id").fetchall()
    return [_task_from_row(row) for row in rows]


def list_sessions(path: Path | str) -> list[dict[str, Any]]:
    with connect(path) as conn:
        rows = conn.execute("select * from sessions order by started_at, id").fetchall()
    return [_session_from_row(row) for row in rows]


def list_worker_adapters(path: Path | str) -> list[dict[str, Any]]:
    with connect(path) as conn:
        rows = conn.execute("select * from worker_adapters order by id").fetchall()
    return [_worker_adapter_from_row(row) for row in rows]


def get_worker_adapter(path: Path | str, adapter_id: str) -> dict[str, Any]:
    with connect(path) as conn:
        row = conn.execute("select * from worker_adapters where id = ?", (adapter_id,)).fetchone()
    if row is None:
        raise KeyError(f"worker adapter not found: {adapter_id}")
    return _worker_adapter_from_row(row)


def update_worker_adapter(
    path: Path | str,
    adapter_id: str,
    *,
    workdir: str | None = None,
    config: dict[str, Any] | None = None,
    supported_models: list[str] | None = None,
    is_default: bool | None = None,
) -> dict[str, Any]:
    updates: list[str] = []
    values: list[Any] = []
    if workdir is not None:
        updates.append("workdir = ?")
        values.append(workdir)
    if config is not None:
        updates.append("config_json = ?")
        values.append(_to_json(config))
    if supported_models is not None:
        updates.append("supported_models_json = ?")
        values.append(json.dumps(supported_models, sort_keys=True, separators=(",", ":")))
    if is_default is not None:
        updates.append("is_default = ?")
        values.append(1 if is_default else 0)
    updates.append("updated_at = ?")
    values.append(_now_iso())

    with connect(path) as conn:
        if is_default:
            conn.execute("update worker_adapters set is_default = 0 where id != ?", (adapter_id,))
        cursor = conn.execute(
            f"update worker_adapters set {', '.join(updates)} where id = ?", (*values, adapter_id)
        )
        if cursor.rowcount == 0:
            raise KeyError(f"worker adapter not found: {adapter_id}")
    return get_worker_adapter(path, adapter_id)


def mark_worker_adapter_verification(
    path: Path | str,
    adapter_id: str,
    *,
    verified: bool,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    now = _now_iso()
    with connect(path) as conn:
        cursor = conn.execute(
            """
            update worker_adapters
            set verification_status = ?, verification_evidence_json = ?, verified_at = ?, updated_at = ?
            where id = ?
            """,
            (
                "verified" if verified else "failed",
                _to_json(_sanitize_evidence(evidence)),
                now if verified else None,
                now,
                adapter_id,
            ),
        )
        if cursor.rowcount == 0:
            raise KeyError(f"worker adapter not found: {adapter_id}")
    return get_worker_adapter(path, adapter_id)


def has_verified_worker_adapter(path: Path | str) -> bool:
    with connect(path) as conn:
        row = conn.execute(
            "select 1 from worker_adapters where verification_status = 'verified' limit 1"
        ).fetchone()
    return row is not None


def has_adapter_verification_token(path: Path | str, *, session_id: str, model: str) -> bool:
    with connect(path) as conn:
        row = conn.execute(
            """
            select 1 from token_turns
            where session_id = ? and usage_kind = 'adapter_verification' and model = ?
            limit 1
            """,
            (session_id, model),
        ).fetchone()
    return row is not None


def list_alarms(
    path: Path | str,
    *,
    session_id: str | None = None,
    alarm_type: str | None = None,
    severity: str | None = None,
    resolved: bool | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    values: list[Any] = []
    if session_id is not None:
        clauses.append("session_id = ?")
        values.append(session_id)
    if alarm_type is not None:
        clauses.append("type = ?")
        values.append(alarm_type)
    if severity is not None:
        clauses.append("severity = ?")
        values.append(severity)
    if resolved is True:
        clauses.append("resolved_at is not null")
    elif resolved is False:
        clauses.append("resolved_at is null")
    where = f" where {' and '.join(clauses)}" if clauses else ""
    query = "select * from alarms" + where + " order by created_at, id"
    with connect(path) as conn:
        rows = conn.execute(query, values).fetchall()
    return [_alarm_from_row(row) for row in rows]


def resolve_alarm(
    path: Path | str,
    *,
    alarm_id: str,
    action: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_at = _now_iso()
    with connect(path) as conn:
        alarm_row = conn.execute("select * from alarms where id = ?", (alarm_id,)).fetchone()
        if alarm_row is None:
            raise KeyError(f"alarm not found: {alarm_id}")
        conn.execute("update alarms set resolved_at = ? where id = ?", (resolved_at, alarm_id))
        cursor = conn.execute(
            """
            insert into action_history (session_id, alarm_id, action, payload_json, created_at)
            values (?, ?, ?, ?, ?)
            """,
            (alarm_row["session_id"], alarm_id, action, _to_json(payload or {}), resolved_at),
        )
        _apply_alarm_action(conn, alarm_row["session_id"], action, payload or {})
        action_row = conn.execute(
            "select * from action_history where id = ?", (cursor.lastrowid,)
        ).fetchone()
        updated_alarm = conn.execute("select * from alarms where id = ?", (alarm_id,)).fetchone()
    return {"alarm": _alarm_from_row(updated_alarm), "action": _action_from_row(action_row)}


def _apply_alarm_action(
    conn: sqlite3.Connection,
    session_id: str,
    action: str,
    payload: dict[str, Any],
) -> None:
    if action == "abort_session":
        conn.execute("update sessions set status = ? where id = ?", ("aborted", session_id))
        return
    if action not in {"raise_budget", "adjust_guardrail"}:
        return

    row = conn.execute("select guardrail_overrides_json from sessions where id = ?", (session_id,)).fetchone()
    if row is None:
        return
    overrides = _from_json(row["guardrail_overrides_json"])
    if action == "raise_budget":
        budget = dict(overrides.get("budget", {}))
        budget.update(payload)
        overrides["budget"] = budget
    else:
        _deep_merge(overrides, payload)
    conn.execute(
        "update sessions set guardrail_overrides_json = ? where id = ?",
        (_to_json(overrides), session_id),
    )


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


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


def total_token_usage(path: Path | str, *, since: str | None = None) -> int:
    with connect(path) as conn:
        if since is None:
            row = conn.execute("select coalesce(sum(total_tokens), 0) as total from token_turns").fetchone()
        else:
            row = conn.execute(
                "select coalesce(sum(total_tokens), 0) as total from token_turns where created_at >= ?",
                (since,),
            ).fetchone()
    return int(row["total"])


def session_token_usage(path: Path | str, session_id: str) -> int:
    with connect(path) as conn:
        row = conn.execute(
            "select coalesce(sum(total_tokens), 0) as total from token_turns where session_id = ?",
            (session_id,),
        ).fetchone()
    return int(row["total"])


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


def _task_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "description": row["description"],
        "status": row["status"],
        "estimate_tokens": row["estimate_tokens"],
        "recommended_model": row["recommended_model"],
        "actual_tokens": row["actual_tokens"],
        "session_id": row["session_id"],
        "metadata": _from_json(row["metadata_json"]),
        "created_at": row["created_at"],
    }


def _token_turn_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "usage_kind": row["usage_kind"],
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
        "session_id": row["session_id"],
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


def _action_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "session_id": row["session_id"],
        "alarm_id": row["alarm_id"],
        "action": row["action"],
        "payload": _from_json(row["payload_json"]),
        "created_at": row["created_at"],
    }


def _worker_adapter_from_row(row: sqlite3.Row) -> dict[str, Any]:
    config = _from_json(row["config_json"])
    supported_models = json.loads(row["supported_models_json"])
    return {
        "id": row["id"],
        "kind": row["kind"],
        "name": row["name"],
        "workdir": row["workdir"],
        "config": config,
        "supported_models": supported_models,
        "is_default": bool(row["is_default"]),
        "verification_status": row["verification_status"],
        "verification_evidence": _from_json(row["verification_evidence_json"]),
        "verified_at": row["verified_at"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "configured": bool(row["workdir"]) or bool(config.get("command")),
    }


SECRET_KEY_TERMS = ("key", "secret", "password", "authorization")
SECRET_TOKEN_KEYS = {"token", "api_token", "access_token", "refresh_token", "session_token"}
SECRET_VALUE_PATTERN = re.compile(r"sk_[A-Za-z0-9_\-.]+")


def _is_secret_key_hint(key_hint: str) -> bool:
    lowered = key_hint.lower()
    return any(term in lowered for term in SECRET_KEY_TERMS) or lowered in SECRET_TOKEN_KEYS or lowered.endswith("_token")


def _sanitize_secret_string(value: str) -> str:
    if "secret" in value.lower():
        return "***REDACTED***"
    return SECRET_VALUE_PATTERN.sub("***REDACTED***", value)


def _sanitize_evidence(value: Any, key_hint: str = "") -> Any:
    if isinstance(value, dict):
        return {k: _sanitize_evidence(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_evidence(item, key_hint) for item in value]
    if isinstance(value, str):
        if _is_secret_key_hint(key_hint):
            return "***REDACTED***"
        return _sanitize_secret_string(value)
    return value


def _to_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _from_json(value: str) -> dict[str, Any]:
    return json.loads(value)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
