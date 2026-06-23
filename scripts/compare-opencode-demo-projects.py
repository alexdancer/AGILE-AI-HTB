#!/usr/bin/env python3
"""Compare direct vs AGILE-AI-HTB OpenCode DEMO 2099 project outputs.

This is an external smoke check: same commands, same pass/fail criteria, no trust
in either project's self-written tests.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECT = ROOT / ".demo/opencode-comparison/direct-target"
HARNESS = ROOT / ".demo/opencode-comparison/harness-target/incident-ledger"
REQUIRED_COMMANDS = ["ingest", "list", "dedupe", "score", "report", "export"]
PYTHON = Path("/usr/bin/python3") if Path("/usr/bin/python3").exists() else Path(sys.executable)


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


def run(project: Path, args: list[str], *, env: dict[str, str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "incident_ledger.cli", *args],
        cwd=project,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def shell(project: Path, args: list[str], *, env: dict[str, str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=project, env=env, text=True, capture_output=True, timeout=timeout)


def ok(cp: subprocess.CompletedProcess[str], contains: str | None = None) -> bool:
    text = cp.stdout + cp.stderr
    return cp.returncode == 0 and (contains is None or contains in text)


def count_duplicate_assignments(db_path: Path) -> int:
    with sqlite3.connect(db_path) as conn:
        columns = [row[1] for row in conn.execute("pragma table_info(incidents)")]
        if "duplicate_group_id" not in columns:
            return 0
        return int(conn.execute("select count(*) from incidents where duplicate_group_id is not null").fetchone()[0])


def compare_project(label: str, project: Path) -> list[Check]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project / "src")
    checks: list[Check] = []

    if not project.exists():
        return [Check("project exists", False, str(project))]

    with tempfile.TemporaryDirectory(prefix=f"compare-{label.lower()}-") as tmp:
        tmpdir = Path(tmp)
        db = tmpdir / "incident-ledger.sqlite"
        out = tmpdir / "out"
        out.mkdir()
        jsonl = project / "examples/demo_incidents_2099.jsonl"
        md = project / "examples/demo_incidents_2099.md"
        invalid = tmpdir / "invalid.jsonl"
        invalid.write_text(
            '{"incident_id":"REAL-1","title":"real-ish","occurred_at":"2026-01-01",'
            '"account_id":"ACCT-123","owner":"Real","status":"open","system":"x",'
            '"impact_summary":"bad","contact_email":"real@example.com","address":"123 Main"}\n',
            encoding="utf-8",
        )

        help_cp = run(project, ["--help"], env=env)
        help_text = help_cp.stdout + help_cp.stderr
        checks.append(Check("help works", help_cp.returncode == 0, first_line(help_text)))
        missing = [cmd for cmd in REQUIRED_COMMANDS if not re.search(rf"\b{re.escape(cmd)}\b", help_text)]
        checks.append(Check("required commands in help", not missing, "missing: " + ", ".join(missing) if missing else "all present"))

        checks.append(Check("JSONL ingest works", ok(run(project, ["ingest", str(jsonl), "--db", str(db)], env=env), "inserted=")))
        checks.append(Check("Markdown ingest works", ok(run(project, ["ingest", str(md), "--db", str(db)], env=env), "inserted=")))
        checks.append(Check("invalid DEMO values rejected", run(project, ["ingest", str(invalid), "--db", str(db), "--strict"], env=env).returncode != 0))
        checks.append(Check("list status filter works", ok(run(project, ["list", "--db", str(db), "--status", "open"], env=env), "DEMO-INC-2099")))

        before = count_duplicate_assignments(db)
        preview = run(project, ["dedupe", "--db", str(db), "--explain"], env=env)
        after = count_duplicate_assignments(db)
        checks.append(Check("dedupe preview is read-only", preview.returncode == 0 and before == after, f"assignments {before}->{after}"))
        apply = run(project, ["dedupe", "--db", str(db), "--apply"], env=env)
        checks.append(Check("dedupe apply persists groups", apply.returncode == 0 and count_duplicate_assignments(db) > 0))

        checks.append(Check("score persists severity", ok(run(project, ["score", "--db", str(db)], env=env))))
        checks.append(Check("markdown report works", ok(run(project, ["report", "--db", str(db), "--format", "markdown", "--output", str(out / "report.md")], env=env)) and (out / "report.md").exists()))
        json_report = run(project, ["report", "--db", str(db), "--format", "json", "--output", str(out / "report.json")], env=env)
        checks.append(Check("JSON report works", json_report.returncode == 0 and parse_json(out / "report.json")))
        checks.append(Check("JSON export works", ok(run(project, ["export", "--db", str(db), "--format", "json", "--output", str(out / "export.json")], env=env)) and parse_json(out / "export.json")))
        checks.append(Check("CSV export works", ok(run(project, ["export", "--db", str(db), "--format", "csv", "--output", str(out / "export.csv")], env=env)) and (out / "export.csv").exists()))

    tests = shell(project, [str(PYTHON), "-m", "pytest", "-q"], env=env, timeout=120)
    match = re.search(r"(\d+) passed", tests.stdout + tests.stderr)
    checks.append(Check("self-tests pass", tests.returncode == 0, match.group(0) if match else first_line(tests.stdout + tests.stderr)))
    checks.append(Check("synthetic-only source scan", synthetic_scan(project)))
    return checks


def first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")[:120]


def parse_json(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True
    except Exception:
        return False


def synthetic_scan(project: Path) -> bool:
    text = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in project.rglob("*")
        if p.is_file()
        and p.suffix in {".py", ".md", ".jsonl", ".toml"}
        and not any(part in {"__pycache__", ".pytest_cache", ".demo"} for part in p.relative_to(project).parts)
    )
    return (
        "DEMO" in text
        and "2099" in text
        and ".invalid" in text
        and not re.search(r"sk-[A-Za-z0-9_-]{12,}|api[_-]?key\s*=", text, re.I)
    )


def print_markdown(results: dict[str, list[Check]]) -> None:
    names = [check.name for check in results["Direct"]]
    print("| Criterion | Direct | Harness |")
    print("|---|---:|---:|")
    for name in names:
        direct = next(c for c in results["Direct"] if c.name == name)
        harness = next(c for c in results["Harness"] if c.name == name)
        print(f"| {name} | {mark(direct)} | {mark(harness)} |")
    for label, checks in results.items():
        passed = sum(1 for c in checks if c.passed)
        print(f"\n{label}: {passed}/{len(checks)} passed")
        for check in checks:
            if not check.passed:
                print(f"- {check.name}: {check.detail or 'failed'}")


def mark(check: Check) -> str:
    suffix = f" ({check.detail})" if check.detail and check.name == "self-tests pass" else ""
    return ("✅" if check.passed else "❌") + suffix


def main() -> int:
    results = {"Direct": compare_project("Direct", DIRECT), "Harness": compare_project("Harness", HARNESS)}
    print_markdown(results)
    return 0 if all(check.passed for checks in results.values() for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
