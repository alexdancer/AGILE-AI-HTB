# DEMO 2099 Simple Task: Markdown Link Checker CLI

> DEMO DATA ONLY — This task, all examples, and all expected fixtures are synthetic. Use only 2099 dates, DEMO names, `.invalid` email addresses, DEMO addresses, and 999-style fake account numbers. Do not use real customer data. Do not call real external services.

## Purpose

Build a tiny local Python CLI project named `mdlink-check`. This is a deliberately small coding task for comparing two execution paths:

1. A coding agent (Claude Code, OpenCode, or Codex) run directly on this task file.
2. The same coding agent launched through Foreman AI HQ using the same task file and a separately configured harness Worker budget.

This SIMPLE task should complete in roughly 1-3 turns. It exists as the low-end anchor of the comparison set. The goal is not to prove token compression on a trivial task. The goal is to show what the harness adds even on a short run: estimate visibility, budget gating, usage authority, launch evidence, and review-state evidence — versus a raw agent run that produces only code and a chat transcript.

## Starting Point for the Worker

Create or update a small local Python project in the working directory. If the directory is empty, create the project. If a minimal scaffold already exists, preserve useful files and implement the missing behavior.

Expected package name:

```text
mdlink_check
```

Expected console command:

```text
mdlink-check
```

Recommended implementation constraints:

- Use the Python standard library only.
- Use `argparse` for CLI parsing.
- Use `pathlib` for filesystem checks, `re` for link extraction, and `json` for JSON output.
- Add pytest tests. If pytest is unavailable in the scaffold, document the setup and still write tests.
- Do not add any third-party dependencies.
- Do not call real external APIs.
- Do not add auth, billing, deployment, web UI, or cloud integrations.
- Do not validate `http://` or `https://` links — internal/relative links only.

## Synthetic Data Rules

All sample data and test fixtures must be obviously fake.

Required markers:

- Dates: use year `2099` only.
- Names: include `DEMO`, such as `DEMO Docs Team`.
- Email addresses: use `.invalid`, such as `demo.docs.2099@example.invalid`.
- Addresses: include `DEMO`, such as `999 DEMO Docs Loop, Demo City, ZZ 99999`.
- Account IDs: use `999`-style values, such as `ACCT-999-2099-0001`.
- Document IDs: use `DEMO-DOC-2099-0001` style values.

Forbidden:

- Real emails.
- Real addresses.
- Real tokens, secrets, passwords, API keys, or connection strings.
- Commands that send data to real external APIs.
- Instructions to publish to any gist, ticket, issue, email, webhook, or cloud object service.

## Product Goal

`mdlink-check` scans Markdown files for internal relative links (such as `[text](./path/to/file.md)`), checks whether the linked files exist on disk relative to the Markdown file's own directory, and reports broken links with line numbers.

The tool should be useful enough for a reviewer to run it end-to-end with DEMO fixtures:

```bash
mdlink-check examples/demo_doc_2099.md
mdlink-check --dir examples/
mdlink-check --dir examples/ --json
```

Exit code contract:

- Exit `0` if all internal links resolve.
- Exit `1` if any internal link is broken.

## Required CLI Commands

### `mdlink-check <file.md>`

Check a single Markdown file.

Behavior:

- Read the file as UTF-8.
- Find all inline Markdown links of the form `[text](target)`.
- Treat a link as internal when the target is a relative path (does not start with `http://`, `https://`, `mailto:`, `#`, or `/`).
- Resolve each internal target relative to the directory containing the Markdown file.
- Strip any `#anchor` fragment from the target before checking existence.
- Report each broken link with: the Markdown file path, the 1-based line number, the link text, and the unresolved target.
- Print a short summary: files checked, links found, links broken.
- Exit `1` if any broken link was found, otherwise `0`.

### `mdlink-check --dir <dir>`

Check all `.md` files in a directory recursively.

Options:

- `--dir <dir>`: Directory to scan recursively for `*.md` files.

Behavior:

- Discover every `*.md` file under `<dir>` in sorted, deterministic order.
- Run the same internal-link check on each file.
- Aggregate results across all files in the summary.
- Exit `1` if any file has any broken link, otherwise `0`.

### `mdlink-check --json`

Emit results as JSON instead of human-readable text. Combine with a single file argument or with `--dir`.

JSON output must include:

- `demo_banner`: a fixed DEMO-only string.
- `files_checked`: integer.
- `links_found`: integer.
- `links_broken`: integer.
- `broken`: an array of objects, each with `file`, `line`, `text`, and `target`.
- `ok`: boolean, `true` when `links_broken` is `0`.

Behavior:

- JSON output must be deterministic (stable key order, sorted `broken` entries by `file` then `line`).
- The process exit code contract is identical to text mode.

## Required Project Files

If creating from scratch, include:

```text
pyproject.toml
README.md
src/mdlink_check/__init__.py
src/mdlink_check/cli.py
src/mdlink_check/checker.py
examples/demo_doc_2099.md
examples/demo_target_2099.md
tests/test_checker.py
```

You may use a different internal module split if the public CLI behavior and tests are equivalent. The single source file plus CLI entry point is the minimum.

## Input Format

A Markdown document containing inline links. Example fixture `examples/demo_doc_2099.md`:

```markdown
# DEMO-DOC-2099-0001 — DEMO Docs Index

Maintained by DEMO Docs Team (demo.docs.2099@example.invalid).

- A working link to [the target doc](./demo_target_2099.md).
- A working link with anchor to [a section](./demo_target_2099.md#demo-section).
- A broken link to [the missing doc](./demo_missing_2099.md).
- An external link to [example](https://example.invalid) that must be ignored.
```

Companion fixture `examples/demo_target_2099.md`:

```markdown
# DEMO Target Doc 2099

## DEMO Section

Synthetic content for account ACCT-999-2099-0001.
```

## Testing Requirements

Write pytest tests covering:

1. A document with all-resolving internal links reports zero broken links and the checker reports success.
2. A document with at least one broken relative link reports it with the correct 1-based line number.
3. External links (`http`, `https`, `mailto`, `#anchor`, absolute `/`) are ignored and never reported as broken.
4. `--json` output contains the required keys and the `broken` array matches the text-mode findings; `--dir` recurses and aggregates across multiple `.md` files.

## README Requirements

The README should include:

- DEMO-only warning.
- Installation/setup commands.
- Example commands using the provided fixtures.
- Explanation of which links count as internal versus ignored.
- Explanation of the exit-code contract.
- Statement that the project is local-only and does not call external APIs.

## Acceptance Criteria

The task is complete when:

- `mdlink-check --help` works and documents the single-file argument, `--dir`, and `--json`.
- Checking a clean fixture exits `0`.
- Checking a fixture with a broken link exits `1` and reports the line number.
- `--dir` recurses through a directory deterministically.
- `--json` emits the required keys and is deterministic.
- Tests pass with `pytest` or the project runner.
- README explains usage and DEMO-only safety.
- No real data, real secrets, or real external service calls are present.

## Stretch Requirements for Larger Token-Usage Runs

If the core task is completed quickly, continue with these optional items in order. Stop when the run budget or operator instructions require stopping.

1. Support reference-style links (`[text][ref]` plus a `[ref]: ./path.md` definition).
2. Add a `--anchor-check` flag that also verifies `#anchor` fragments match a heading in the target file.
3. Add a `--ignore <glob>` option to skip matching files during `--dir` scans.
4. Add a summary line counting how many links were ignored as external.
5. Add a golden-file test for the `--json` output of the DEMO fixture.
6. Add a fixture with 20 deterministic `DEMO-DOC-2099-*` links, half broken, and a test asserting the count.
7. Add a short `docs/DEMO_2099_OPERATOR_NOTES.md` describing the local-only demo.

## Worker Instructions

Work like a careful coding agent:

- Inspect the current project before editing.
- Make focused changes.
- Prefer simple, deterministic implementation over cleverness.
- Run tests and fix failures.
- Do not commit changes unless explicitly asked.
- Do not call external services.
- Do not use real customer-like examples.
- If blocked, report the exact command and error.

## Expected Final Response From Worker

When finished, summarize:

- files changed;
- commands run;
- test results;
- implemented CLI commands;
- any incomplete stretch items;
- confirmation that all examples are synthetic DEMO 2099 data.
