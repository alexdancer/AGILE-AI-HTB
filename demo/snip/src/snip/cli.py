from __future__ import annotations

import argparse
from collections.abc import Sequence

COMMANDS = ("save", "list", "search", "delete")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snip",
        description="DEMO synthetic snippet manager scaffold for Token Tracker Harness exercises.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in COMMANDS:
        subparsers.add_parser(command, help=f"DEMO scaffold placeholder for snip {command}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    print(f"DEMO scaffold: snip {args.command} is not implemented yet.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
