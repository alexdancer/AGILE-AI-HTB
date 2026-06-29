from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

MAX_DOC_CHARS = 2_000
MAX_BRIEF_CHARS = 8_000
DOC_CANDIDATES = (
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    "README.md",
    "README.rst",
    "docs/README.md",
)
MANIFEST_CANDIDATES = (
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "requirements.txt",
    "uv.lock",
)
ENTRYPOINT_CANDIDATES = (
    "src",
    "app",
    "tests",
    "Dockerfile",
    "docker-compose.yml",
)
SECRET_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}
SECRET_VALUE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(sk-[A-Za-z0-9_.-]+|sk_[A-Za-z0-9_.-]+|Bearer\s+[A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
SECRET_ASSIGNMENT_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer\s+)?)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|access[_-]?token|refresh[_-]?token|session[_-]?token|password|secret)\s*[:=]\s*)[^\s,;]+"),
)
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}


def build_repo_context_brief(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    documents = [_read_doc(root, relative) for relative in DOC_CANDIDATES]
    documents = [doc for doc in documents if doc is not None]
    manifests = [relative for relative in MANIFEST_CANDIDATES if (root / relative).is_file()]
    entrypoints = [relative for relative in ENTRYPOINT_CANDIDATES if (root / relative).exists()]
    tracked_files = _tracked_files(root)
    brief = {
        "project_root": str(root),
        "documents": documents,
        "manifests": manifests,
        "entrypoints": entrypoints,
        "test_commands": _detect_test_commands(root, manifests),
        "tracked_files_sample": tracked_files[:40],
        "omitted": {"secret_files": sorted(name for name in SECRET_NAMES if (root / name).exists())},
    }
    return {**brief, "text": _render_brief(brief)}


def repo_context_prompt(task_prompt: str, brief: dict[str, Any]) -> str:
    text = str(brief.get("text") or "").strip()
    if not text:
        return task_prompt
    return (
        "Repo Context Brief (read this before editing; prefer explicit repo instructions over guesses):\n"
        f"{text}\n\n---\nTask instructions:\n{task_prompt.strip()}"
    )


def _read_doc(root: Path, relative: str) -> dict[str, str] | None:
    path = root / relative
    if not path.is_file() or path.name in SECRET_NAMES:
        return None
    try:
        content = path.read_text(encoding="utf-8", errors="replace")[:MAX_DOC_CHARS]
    except OSError:
        return None
    return {"path": relative, "excerpt": _redact_secret_text(content.strip())}


def _redact_secret_text(text: str) -> str:
    redacted = SECRET_VALUE_PATTERN.sub("***REDACTED***", text)
    for pattern in SECRET_ASSIGNMENT_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}***REDACTED***", redacted)
    return redacted


def _detect_test_commands(root: Path, manifests: list[str]) -> list[str]:
    commands: list[str] = []
    if "pyproject.toml" in manifests:
        commands.append("pytest")
    if "package.json" in manifests:
        try:
            package = json.loads((root / "package.json").read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            package = {}
        scripts = package.get("scripts") if isinstance(package, dict) else {}
        if isinstance(scripts, dict) and "test" in scripts:
            commands.append("npm test")
    if "Cargo.toml" in manifests:
        commands.append("cargo test")
    if "go.mod" in manifests:
        commands.append("go test ./...")
    return commands


def _tracked_files(root: Path) -> list[str]:
    files: list[str] = []
    for path in root.rglob("*"):
        if len(files) >= 80:
            break
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if path.name in SECRET_NAMES:
            continue
        files.append(str(relative))
    return sorted(files)


def _render_brief(brief: dict[str, Any]) -> str:
    sections: list[str] = [f"Project root: {brief['project_root']}"]
    if brief["documents"]:
        sections.append("Repo instructions/docs:")
        for doc in brief["documents"]:
            sections.append(f"- {doc['path']}:\n{doc['excerpt']}")
    if brief["manifests"]:
        sections.append("Manifests: " + ", ".join(brief["manifests"]))
    if brief["entrypoints"]:
        sections.append("Likely entry points: " + ", ".join(brief["entrypoints"]))
    if brief["test_commands"]:
        sections.append("Detected verification commands: " + ", ".join(brief["test_commands"]))
    if brief["tracked_files_sample"]:
        sections.append("Repository file sample:\n" + "\n".join(f"- {item}" for item in brief["tracked_files_sample"]))
    text = "\n\n".join(sections).strip()
    return text[:MAX_BRIEF_CHARS]
