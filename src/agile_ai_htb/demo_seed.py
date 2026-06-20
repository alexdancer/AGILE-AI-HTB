from __future__ import annotations

import json
from pathlib import Path

from agile_ai_htb import db

DEMO_TASKS = (
    {
        "id": "DEMO_TASK_2099_T1",
        "description": "Implement `snip save` — accept title, language, and body via CLI args; write snippet to the store",
        "complexity": "Simple",
        "estimate_tokens": 8_000,
        "recommended_model": "Claude Haiku",
    },
    {
        "id": "DEMO_TASK_2099_T2",
        "description": "Add a `--color` flag — support `--color/--no-color` for terminal output; pass through to rich.print",
        "complexity": "Simple",
        "estimate_tokens": 5_000,
        "recommended_model": "Claude Haiku",
    },
    {
        "id": "DEMO_TASK_2099_T3",
        "description": "Implement `snip list` with filters — list all snippets; support `--language` and `--tag` filters; format as a table with rich",
        "complexity": "Modest",
        "estimate_tokens": 25_000,
        "recommended_model": "Claude Sonnet",
    },
    {
        "id": "DEMO_TASK_2099_T4",
        "description": "Add fuzzy search via `snip search` — accept a query string; use thefuzz for fuzzy matching on title and body; rank and display results",
        "complexity": "Modest",
        "estimate_tokens": 35_000,
        "recommended_model": "Claude Sonnet",
    },
    {
        "id": "DEMO_TASK_2099_T5",
        "description": "Add SQLite backend with migration — replace JSON file store with sqlite3; import existing DEMO JSON snippets; add `--db-path` flag",
        "complexity": "Complex",
        "estimate_tokens": 90_000,
        "recommended_model": "Claude Opus",
    },
    {
        "id": "DEMO_TASK_2099_T6",
        "description": "Add `snip share` with DEMO gist integration — accept a snippet ID; call a fake GitHub Gist seam; require a demo token env var",
        "complexity": "Complex",
        "estimate_tokens": 80_000,
        "recommended_model": "Claude Opus",
    },
)


def seed_demo_tasks(db_path: Path | str) -> list[dict[str, object]]:
    """Insert the six synthetic DEMO snip tasks if absent.

    Returns only tasks inserted during this call, making the function idempotent
    and easy for operators/tests to verify.
    """
    db.init_db(db_path)
    _seed_demo_worker_adapter(db_path)
    inserted_ids: list[str] = []
    with db.connect(db_path) as conn:
        for task in DEMO_TASKS:
            existing = conn.execute("select id from tasks where id = ?", (task["id"],)).fetchone()
            if existing is not None:
                continue
            conn.execute(
                """
                insert into tasks (
                    id, description, status, estimate_tokens, recommended_model,
                    actual_tokens, session_id, metadata_json, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task["id"],
                    task["description"],
                    "Estimated",
                    task["estimate_tokens"],
                    task["recommended_model"],
                    None,
                    None,
                    json.dumps(
                        {"complexity": task["complexity"], "demo": "DEMO_SNIP_2099"},
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                    "2099-06-13T00:00:00+00:00",
                ),
            )
            inserted_ids.append(task["id"])
    return [db.get_task(db_path, task_id) for task_id in inserted_ids]


def _seed_demo_worker_adapter(db_path: Path | str) -> None:
    """Ensure a verified demo worker adapter exists for the portal launch flow."""
    with db.connect(db_path) as conn:
        conn.execute(
            """insert into worker_adapters
               (id, kind, name, config_json, supported_models_json, workdir,
                verification_status, verification_evidence_json, is_default, created_at, updated_at)
               values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               on conflict(id) do update set
                   config_json = excluded.config_json,
                   supported_models_json = excluded.supported_models_json,
                   workdir = excluded.workdir,
                   verification_status = excluded.verification_status,
                   verification_evidence_json = excluded.verification_evidence_json,
                   is_default = excluded.is_default,
                   updated_at = excluded.updated_at""",
            (
                "demo_worker",
                "demo_worker",
                "Demo Worker",
                json.dumps(
                    {
                        "command": "htb-demo-worker",
                        "verification_template": ["htb-demo-worker", "--prompt", "{prompt}", "--proxy-url", "{proxy_url}", "--session-key", "{session_api_key}", "--turns", "1", "--dry-run"],
                        "launch_template": ["htb-demo-worker", "--prompt", "{prompt}", "--proxy-url", "{proxy_url}", "--session-key", "{session_api_key}", "--model", "{model}"],
                        "launch_timeout_seconds": 360,
                    },
                    separators=(",", ":"),
                ),
                json.dumps(
                    [
                        "gpt-5.4-mini",
                        "gpt-4o-mini",
                        "gpt-4o",
                        "claude-3-haiku-20240307",
                        "claude-3-5-sonnet-20240620",
                    ],
                    separators=(",", ":"),
                ),
                "/tmp",
                "verified",
                json.dumps(
                    {
                        "tracking_mode": "proxy_governed",
                        "tracking_authoritative": True,
                        "token_recorded": True,
                        "source": "synthetic_demo_seed",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                1,
                "2099-06-13T00:00:00+00:00",
                "2099-06-13T00:00:00+00:00",
            ),
        )
