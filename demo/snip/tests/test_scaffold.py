from __future__ import annotations

from pathlib import Path

from snip.cli import main
from snip.store import SnippetStore


def test_cli_exposes_demo_placeholder_commands(capsys):
    for command in ["save", "list", "search", "delete"]:
        exit_code = main([command])
        captured = capsys.readouterr()

        assert exit_code == 2
        assert "DEMO scaffold" in captured.out
        assert "not implemented yet" in captured.out
        assert command in captured.out


def test_store_constructor_uses_synthetic_demo_path(tmp_path):
    store_path = tmp_path / "DEMO_SNIP_2099_STORE"

    store = SnippetStore(store_path)

    assert store.root == store_path
    assert store.root.name == "DEMO_SNIP_2099_STORE"


def test_scaffold_files_are_small_and_safe():
    root = Path(__file__).resolve().parents[1]

    assert (root / "src" / "snip" / "cli.py").read_text().count("not implemented") >= 1
    assert "GITHUB_TOKEN" not in (root / "src" / "snip" / "cli.py").read_text()
