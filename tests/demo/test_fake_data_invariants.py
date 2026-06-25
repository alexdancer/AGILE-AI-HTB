from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "demo"
LONG_OPENCODE_COMPARISON_FILES = [
    ROOT / "demo_tasks" / "DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md",
    ROOT / "docs" / "DEMO_2099_OPENCODE_COMPARISON_RUNBOOK.md",
]
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


class LongOpenCodeComparisonFakeDataInvariantTests:
    __test__ = True

    def test_long_opencode_comparison_artifacts_exist(self) -> None:
        missing = [path.relative_to(ROOT).as_posix() for path in LONG_OPENCODE_COMPARISON_FILES if not path.is_file()]
        assert missing == []

    def test_long_opencode_comparison_uses_obvious_demo_markers(self) -> None:
        for path in LONG_OPENCODE_COMPARISON_FILES:
            text = path.read_text()
            assert "DEMO" in text
            assert "2099" in text
            assert ".invalid" in text
            assert "999" in text
            assert "real customer data" in text.lower()

    def test_long_opencode_comparison_has_no_real_looking_years_or_emails(self) -> None:
        text = "\n".join(path.read_text() for path in LONG_OPENCODE_COMPARISON_FILES)
        real_years = re.findall(r"\b20(?:2[0-8])\b", text)
        non_demo_emails = [
            email
            for email in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
            if not email.endswith(".invalid")
        ]
        assert real_years == []
        assert non_demo_emails == []

    @pytest.mark.parametrize("pattern", BANNED_SECRET_PATTERNS)
    def test_long_opencode_comparison_has_no_real_looking_secrets(self, pattern: re.Pattern[str]) -> None:
        offenders: list[str] = []
        allowed_demo_assignments = {
            'TOKEN_TRACKER_PORTAL_TOKEN="demo-token"',
            'TOKEN_TRACKER_PORTAL_TOKEN="demo-token"',
        }
        for path in LONG_OPENCODE_COMPARISON_FILES:
            for line in path.read_text().splitlines():
                if "TOKEN_TRACKER_PORTAL_TOKEN" in line and "demo-token" in line:
                    continue
                if line.strip() in allowed_demo_assignments:
                    continue
                if pattern.search(line):
                    offenders.append(f"{path.relative_to(ROOT).as_posix()}: {line.strip()}")
        assert offenders == []

    def test_long_opencode_comparison_forbids_real_external_service_calls(self) -> None:
        text = "\n".join(path.read_text() for path in LONG_OPENCODE_COMPARISON_FILES).lower()
        forbidden_instruction_snippets = [
            "curl https://",
            "curl -x post https://",
            "requests.post(\"https://",
            "requests.get(\"https://",
            "publish a real gist",
            "create a real github issue",
            "send a real email",
        ]
        offenders = [snippet for snippet in forbidden_instruction_snippets if snippet in text]
        assert offenders == []

    def test_long_opencode_comparison_requires_harness_target_workdir_evidence(self) -> None:
        runbook = (ROOT / "docs" / "DEMO_2099_OPENCODE_COMPARISON_RUNBOOK.md").read_text().lower()

        assert "opencode run --dir" in runbook
        assert ".demo/opencode-comparison/harness-target" in runbook
        assert "retryable workdir mismatch" in runbook
        assert "do not count repo-level `incident-ledger/` output as successful harness evidence" in runbook
