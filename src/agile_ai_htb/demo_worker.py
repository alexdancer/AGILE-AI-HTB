"""Demo worker: lightweight proxy caller for harness demos.

This simulates a coding agent by making OpenAI-compatible requests to the
harness proxy. It exercises the full governance path — zone transitions,
token tracking, tool restrictions, alarm firing — with real LLM calls
through the direct-provider harness proxy.

Usage:
    htb-demo-worker \\
        --prompt "Add a save command to the CLI" \\
        --proxy-url http://127.0.0.1:8000/v1 \\
        --session-key sk_sess_abc123 \\
        --model gpt-4o-mini
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Sequence
from urllib.request import Request, urlopen


def _post(url: str, payload: dict, *, headers: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=headers or {})
    req.add_header("Content-Type", "application/json")
    with urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _tool(name: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": f"Synthetic DEMO tool named {name}.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    }


def demo_worker(
    *,
    prompt: str,
    proxy_url: str,
    session_key: str,
    model: str,
    turns: int = 3,
    dry_run: bool = False,
) -> int:
    """Run a demo worker session through the harness proxy.

    Makes `turns` proxy requests with different tool sets to exercise
    governance (zone transitions, tool blocking, prompt rewrites).
    """
    auth_headers = {"Authorization": f"Bearer {session_key}"}
    endpoint = f"{proxy_url.rstrip('/')}/chat/completions"

    # Turn 1: Full tools — green zone, no restrictions
    response = _post(
        endpoint,
        {
            "model": model,
            "messages": [
                {"role": "system", "content": f"You are a coding agent. Task: {prompt}"},
                {"role": "user", "content": "Let me start by reading the existing codebase structure."},
            ],
            "tools": [_tool("read_file"), _tool("search_files"), _tool("web_search")],
        },
        headers=auth_headers,
    )
    if dry_run:
        print(f"[turn 1] status=ok content={_content(response)[:80]}")
    time.sleep(0.5)

    if turns < 2:
        return 0

    # Turn 2: Implementation tools — patch, terminal, read_file
    _post(
        endpoint,
        {
            "model": model,
            "messages": [
                {"role": "user", "content": "Now implement the change using patch and verify with terminal."},
            ],
            "tools": [_tool("read_file"), _tool("patch"), _tool("terminal")],
        },
        headers=auth_headers,
    )
    if dry_run:
        print("[turn 2] status=ok")
    time.sleep(0.5)

    if turns < 3:
        return 0

    # Turn 3: Verification — terminal only
    _post(
        endpoint,
        {
            "model": model,
            "messages": [
                {"role": "user", "content": "Run the tests to verify everything works."},
            ],
            "tools": [_tool("terminal")],
        },
        headers=auth_headers,
    )
    if dry_run:
        print("[turn 3] status=ok")

    return 0


def _content(response: dict) -> str:
    choices = response.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="htb-demo-worker",
        description="Demo worker for AGILE-AI-HTB harness proxy.",
    )
    parser.add_argument("--prompt", required=True, help="Task description prompt.")
    parser.add_argument("--proxy-url", required=True, help="Harness proxy base URL (e.g. http://127.0.0.1:8000/v1).")
    parser.add_argument("--session-key", required=True, help="Session API key (sk_sess_*).")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model to use (default: gpt-4o-mini).")
    parser.add_argument("--turns", type=int, default=3, help="Number of proxy requests (default: 3).")
    parser.add_argument("--dry-run", action="store_true", help="Print turn summaries instead of full output.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    return demo_worker(
        prompt=args.prompt,
        proxy_url=args.proxy_url,
        session_key=args.session_key,
        model=args.model,
        turns=args.turns,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
