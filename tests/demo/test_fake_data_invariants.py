from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "demo"
IGNORED_PARTS = {".venv", ".pytest_cache", "__pycache__"}

BANNED_SECRET_PATTERNS = [
    re.compile(r"sk-(?:live|proj|test)-[A-Za-z0-9_-]{12,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{6,}['\"]"),
]


class TokenTrackerHarnessDemoFakeDataInvariantTests:
    __test__ = True

    def test_demo_directory_exists(self) -> None:
        assert DEMO_DIR.is_dir()

    def test_no_env_files_under_demo(self) -> None:
        offenders = [path for path in DEMO_DIR.rglob("*") if path.name.startswith(".env")]
        assert offenders == []

    def test_demo_files_contain_synthetic_banner_or_demo_marker(self) -> None:
        text_files = [path for path in _demo_source_files() if path.suffix in {".py", ".toml", ".md"}]
        assert text_files, "demo must contain inspectable text files"
        offenders = []
        for path in text_files:
            text = path.read_text()
            if "DEMO" not in text and "synthetic" not in text.lower():
                offenders.append(path.relative_to(ROOT).as_posix())
        assert offenders == []

    @pytest.mark.parametrize("pattern", BANNED_SECRET_PATTERNS)
    def test_demo_files_do_not_contain_real_looking_secrets(self, pattern: re.Pattern[str]) -> None:
        offenders: list[str] = []
        for path in _demo_source_files():
            if path.suffix not in {".py", ".toml", ".md"}:
                continue
            text = path.read_text()
            if pattern.search(text):
                offenders.append(path.relative_to(ROOT).as_posix())
        assert offenders == []

    def test_demo_source_does_not_use_real_home_snip_path(self) -> None:
        offenders: list[str] = []
        for path in _demo_source_files():
            if path.suffix != ".py":
                continue
            text = path.read_text()
            if "~/.snip" in text or "Path.home()" in text:
                offenders.append(path.relative_to(ROOT).as_posix())
        assert offenders == []


def _demo_source_files() -> list[Path]:
    return [
        path
        for path in DEMO_DIR.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_PARTS or part.endswith(".egg-info") for part in path.parts)
    ]
