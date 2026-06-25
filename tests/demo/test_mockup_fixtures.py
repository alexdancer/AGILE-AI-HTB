"""AGILE-AI-HTBDemoFakeDataInvariantTests.

Guards the rule that every value surfaced by the AGILE-AI-HTB mockup is
obviously synthetic. Half-real/half-fake demos are not acceptable; this
scans the mockup fixtures for any value that could plausibly be a real
session ID, account number, or timestamp in the present year.

If you add new fixtures to docs/mockup/js/fixtures.js, add or update the
patterns below. The test runs as part of `pytest` — keep it green.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest


MOCKUP_DIR = Path(__file__).resolve().parents[2] / "docs" / "mockup"
FIXTURES_PATH = MOCKUP_DIR / "js" / "fixtures.js"

# Every fake ID should be prefixed with DEMO_ + year-2099 + underscore.
ID_PATTERN = re.compile(r"^DEMO_[A-Z]+_2099_[a-zA-Z0-9]+$")

# Anything in the fixtures that looks like a real production hostname,
# email, or "live" status word is suspect.
BANNED_WORDS = ("prod", "production", "live", "staging", "stg", "real-")


def _load_fixtures() -> dict[str, Any]:
    """Eval the fixtures.js file in a controlled way to extract AGILE_AI_HTB.fixtures.

    We don't have a JS runtime in pytest, so we do a minimal parse: grab the
    object literal assigned to `fixtures:` inside `AGILE_AI_HTB = {...}`. The
    fixtures file is hand-written and small, so a hand-rolled extractor is
    fine — the goal is to scan *string values*, not to faithfully execute JS.
    """
    text = FIXTURES_PATH.read_text()

    # Grab everything between the outermost `{` and the matching `}` after
    # the `fixtures` key. The file assigns `window.AGILE_AI_HTB.fixtures
    # = { ... }` so we match `fixtures` followed by `=` (with optional
    # whitespace) and a brace. This is a deliberately loose parse — we
    # only care about the string literals inside.
    match = re.search(r"fixtures\s*=\s*\{", text)
    assert match, "fixtures.js must define `fixtures = { ... }`"

    start = match.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    body = text[start : i - 1]

    # Pull out every double-quoted string in the fixtures body.
    strings = re.findall(r'"((?:[^"\\]|\\.)*)"', body)
    return {"_raw_strings": strings}


class AGILE_AI_HTBDemoFakeDataInvariantTests:
    """All mockup fixture data must be obviously synthetic."""

    # pytest's default python_classes is startswith("Test"), which would
    # skip a class named <DemoName>FakeDataInvariantTests. __test__ = True
    # opts the class in explicitly without renaming it.
    __test__ = True

    @pytest.fixture(scope="class")
    def fixtures(self) -> dict[str, Any]:
        return _load_fixtures()

    def test_fixtures_file_exists(self) -> None:
        assert FIXTURES_PATH.is_file(), f"missing {FIXTURES_PATH}"

    def test_every_id_is_demo_prefixed(self, fixtures: dict[str, Any]) -> None:
        """Session / alarm / task IDs must all match DEMO_*_2099_* pattern."""
        offenders: list[str] = []
        for s in fixtures["_raw_strings"]:
            # An "ID-looking" string is anything that contains a year-2099
            # token OR a DEMO prefix. Reject if it has a year-2099 token but
            # is missing the DEMO prefix, or vice versa.
            if "_2099_" in s and not s.startswith("DEMO_"):
                offenders.append(s)
            if s.startswith("DEMO_") and "_2099_" not in s:
                # Allow short labels like "DEMO_PORTAL" but flag anything
                # that *looks* like an ID (more than 8 chars, has digits).
                if re.search(r"\d", s) and len(s) > 8:
                    offenders.append(s)
        assert not offenders, (
            "fixture strings look like real IDs but are not DEMO_..._2099_...:\n"
            + "\n".join(sorted(set(offenders)))
        )

    def test_no_real_year_timestamps(self, fixtures: dict[str, Any]) -> None:
        """Timestamps should be in 2099. Anything 2024-2028 is suspect."""
        offenders = [
            s for s in fixtures["_raw_strings"]
            if re.search(r"\b(202[4-8])-", s)
        ]
        assert not offenders, (
            "fixture contains a present-year timestamp:\n"
            + "\n".join(sorted(set(offenders)))
        )

    def test_no_prod_or_live_words(self, fixtures: dict[str, Any]) -> None:
        """No fixture value should claim to be production or live."""
        offenders: list[str] = []
        for s in fixtures["_raw_strings"]:
            s_low = s.lower()
            for banned in BANNED_WORDS:
                if banned in s_low:
                    offenders.append(f"{banned!r} in {s!r}")
        assert not offenders, "banned words:\n" + "\n".join(sorted(set(offenders)))

    def test_dashboard_banner_is_present_in_html(self) -> None:
        """Every page must show a DEMO banner."""
        for html in MOCKUP_DIR.glob("*.html"):
            content = html.read_text()
            assert "DEMO" in content and "synthetic" in content.lower(), (
                f"{html.name} is missing the DEMO banner"
            )

    def test_no_html_page_references_live_api(self) -> None:
        """Mockup pages should be self-contained — no live fetch() URLs."""
        for html in MOCKUP_DIR.glob("*.html"):
            content = html.read_text()
            assert "fetch(" not in content and "http://" not in content and "https://" not in content, (
                f"{html.name} appears to make a live network call"
            )
