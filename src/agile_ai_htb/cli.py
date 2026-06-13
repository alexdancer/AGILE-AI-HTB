from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Sequence

import uvicorn

from agile_ai_htb.demo_seed import seed_demo_tasks

APP_REF = "agile_ai_htb.app:create_app"


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    command = args.command or "serve"

    if command == "serve":
        database_path = _arg_path(args, "serve_database_path", "global_database_path")
        guardrails_path = _arg_path(args, "serve_guardrails_path", "global_guardrails_path")
        _set_path_env("TOKEN_TRACKER_DATABASE_PATH", database_path)
        _set_path_env("TOKEN_TRACKER_GUARDRAILS_PATH", guardrails_path)
        uvicorn.run(
            APP_REF,
            host=getattr(args, "host", "127.0.0.1"),
            port=getattr(args, "port", 8000),
            proxy_headers=getattr(args, "proxy_headers", False),
            factory=True,
            env_file=None,
        )
        return 0

    if command == "seed-demo":
        database_path = _arg_path(args, "seed_database_path", "global_database_path")
        db_path = Path(database_path or os.getenv("TOKEN_TRACKER_DATABASE_PATH", "harness.db"))
        inserted = seed_demo_tasks(db_path)
        print(f"seed-demo inserted {len(inserted)} synthetic DEMO tasks into {db_path}")
        return 0

    parser.error(f"unknown command: {command}")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="htb",
        description="AGILE-AI-HTB operator command. Bare htb starts the portal server.",
    )
    parser.add_argument(
        "--database-path",
        dest="global_database_path",
        default=None,
        help="SQLite database path. Overrides TOKEN_TRACKER_DATABASE_PATH.",
    )
    parser.add_argument(
        "--guardrails-path",
        dest="global_guardrails_path",
        default=None,
        help="Guardrails YAML path. Overrides TOKEN_TRACKER_GUARDRAILS_PATH.",
    )
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="Run AGILE-AI-HTB portal/API server.")
    serve.add_argument("--host", default="127.0.0.1", help="Bind host.")
    serve.add_argument("--port", type=int, default=8000, help="Bind port.")
    serve.add_argument(
        "--proxy-headers",
        action="store_true",
        default=False,
        help="Trust X-Forwarded-* headers from reverse proxy.",
    )
    serve.add_argument(
        "--database-path",
        dest="serve_database_path",
        default=None,
        help="SQLite database path. Overrides TOKEN_TRACKER_DATABASE_PATH.",
    )
    serve.add_argument(
        "--guardrails-path",
        dest="serve_guardrails_path",
        default=None,
        help="Guardrails YAML path. Overrides TOKEN_TRACKER_GUARDRAILS_PATH.",
    )

    seed_demo = subparsers.add_parser("seed-demo", help="Insert synthetic DEMO snip tasks.")
    seed_demo.add_argument(
        "--database-path",
        dest="seed_database_path",
        default=None,
        help="SQLite database path. Overrides TOKEN_TRACKER_DATABASE_PATH.",
    )
    return parser


def _arg_path(args: argparse.Namespace, primary: str, fallback: str) -> str | None:
    return getattr(args, primary, None) or getattr(args, fallback, None)


def _set_path_env(name: str, value: str | None) -> None:
    if value:
        os.environ[name] = str(Path(value))
