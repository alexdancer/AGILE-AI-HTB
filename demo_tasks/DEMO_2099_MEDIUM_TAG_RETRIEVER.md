# DEMO 2099 Medium Task: Hermes Tag Retriever CLI

> DEMO DATA ONLY — This task, all examples, and all expected fixtures are synthetic. Use only 2099 dates, DEMO names, `.invalid` email addresses, DEMO addresses, and 999-style fake account numbers. Do not use real customer data. Do not call real external services.

## Purpose

Build a local Python CLI project named `tag-retriever` (the "Hermes Tag Retriever"). This is a medium-sized coding task for comparing two execution paths:

1. A coding agent (Claude Code, OpenCode, or Codex) run directly on this task file.
2. The same coding agent launched through AGILE-AI-HTB using the same task file and a separately configured harness Worker budget.

This MEDIUM task should take roughly 5-12 turns. It is the middle anchor of the comparison set: enough real implementation work (subcommands, a SQLite schema, a hand-rolled YAML-ish parser, regex extraction, deterministic output) to produce meaningful token usage, while still being achievable in one sitting. The goal is to show what the harness adds on a moderate run: estimate visibility, budget gating, usage authority, launch evidence, alarms or overrides, and review-state evidence — versus a raw agent run that produces only code and a chat transcript.

## Starting Point for the Worker

Create or update a small local Python project in the working directory. If the directory is empty, create the project. If a minimal scaffold already exists, preserve useful files and implement the missing behavior.

Expected package name:

```text
tag_retriever
```

Expected console command:

```text
tag-retriever
```

Recommended implementation constraints:

- Use the Python standard library where practical.
- Use `argparse` with subcommands for CLI parsing.
- Use `sqlite3` for persistence.
- Use `re`, `json`, `csv`, `datetime`, and `pathlib` as needed.
- Do NOT use any external YAML library (no `pyyaml`). Parse YAML-like frontmatter with a simple, deterministic line-based parser that handles only the structures described below.
- Add pytest tests. If pytest is unavailable in the scaffold, document the setup and still write tests.
- Do not add network dependencies.
- Do not call real external APIs.
- Do not add auth, billing, deployment, web UI, or cloud integrations.

## Synthetic Data Rules

All sample data and test fixtures must be obviously fake.

Required markers:

- Dates: use year `2099` only.
- Names: include `DEMO`, such as `DEMO Knowledge Ops`.
- Email addresses: use `.invalid`, such as `demo.knowledge.2099@example.invalid`.
- Addresses: include `DEMO`, such as `999 DEMO Archive Way, Demo City, ZZ 99999`.
- Account IDs: use `999`-style values, such as `ACCT-999-2099-0001`.
- Document IDs: use `DEMO-NOTE-2099-0001` style values.

Forbidden:

- Real emails.
- Real addresses.
- Real tokens, secrets, passwords, API keys, or connection strings.
- Commands that send data to real external APIs.
- Instructions to publish to any gist, ticket, issue, email, webhook, or cloud object service.

## Product Goal

`tag-retriever` builds an inverted index of tags across a tree of Markdown notes and supports search, statistics, change detection, and export. Tags come from two sources in each note:

1. YAML-like frontmatter at the top of the file (`tags: [a, b, c]` inline list, or a block list with `- a` lines).
2. Inline `#tag` style tags in the body text.

The tool should be useful enough for a reviewer to run it end-to-end with DEMO fixtures:

```bash
tag-retriever index examples/notes_2099 --db .demo/tag-retriever.sqlite
tag-retriever find "python,testing" --db .demo/tag-retriever.sqlite
tag-retriever stats --db .demo/tag-retriever.sqlite
tag-retriever diff examples/notes_2099 --db .demo/tag-retriever.sqlite
tag-retriever export --format json --db .demo/tag-retriever.sqlite
tag-retriever export --format csv --db .demo/tag-retriever.sqlite
```

## Required CLI Commands

The CLI uses `argparse` subcommands. Every subcommand accepts `--db <path>` (default `.tag-retriever.sqlite` in the current directory).

### `tag-retriever index <dir>`

Ingest: scan a directory tree recursively for `*.md` files and build the index.

Options:

- `--db <path>`
- `--dry-run`: Parse and report what would be indexed without writing rows.

Behavior:

- Create the database and schema if missing.
- For each `*.md` file, extract tags from frontmatter and inline `#tag` tokens.
- Normalize tags to lowercase and de-duplicate per file.
- Store the file→tags mapping with an `indexed_at` timestamp and a content hash.
- On re-index, update existing files and remove rows for files that no longer exist.
- Print a summary: files scanned, files indexed, total distinct tags.

### `tag-retriever find "<tags>"`

Search: list files matching ALL of the comma-separated tags (AND logic).

Options:

- `--db <path>`
- `--json`: Emit JSON instead of table text.

Behavior:

- Split the query on commas, trim whitespace, lowercase each tag.
- Return only files that contain every queried tag.
- Sort matches by recency (most recently indexed first), then by file path ascending for ties.
- A single-tag query returns all files carrying that tag.
- If nothing matches, print a clear empty-state message and exit `0`.

### `tag-retriever stats`

Statistics: print a tag frequency histogram as a Markdown table.

Options:

- `--db <path>`

Behavior:

- Output a Markdown table with header row `| Tag | Files |` and a separator row.
- One row per distinct tag with the count of files carrying it.
- Sort by count descending, then tag ascending.
- Output must be deterministic.

### `tag-retriever diff <dir>`

Watch/diff: show files whose tags changed since the last index.

Options:

- `--db <path>`

Behavior:

- Re-scan the directory and compare each file's current tags against the stored index.
- Report three groups: `added` (new files), `removed` (indexed files now missing), and `changed` (files whose tag set differs).
- For `changed` files, show the added and removed tags.
- If nothing changed, print a clear "no changes" message and exit `0`.
- `diff` is read-only and must not mutate the index.

### `tag-retriever export`

Export: dump the full index.

Options:

- `--db <path>`
- `--format json|csv`
- `--output <path>`: optional; if omitted, print to stdout.

Behavior:

- JSON export: an array of objects, each with `file`, `tags` (sorted array), `indexed_at`, and `content_hash`.
- CSV export: stable headers `file,tags,indexed_at,content_hash`; the `tags` column is a sorted, semicolon-joined string.
- Output must be deterministic (files sorted by path).
- Create parent directories for `--output` if missing.

## Frontmatter and Inline Tag Format

### Frontmatter (YAML-like)

Frontmatter is delimited by lines containing only `---` at the very top of the file. The parser must handle exactly these `tags` forms and ignore other keys.

Inline list form:

```markdown
---
id: DEMO-NOTE-2099-0001
title: DEMO synthetic onboarding note
owner: DEMO Knowledge Ops
tags: [python, testing, demo]
---

Body text for ACCT-999-2099-0001.
```

Block list form:

```markdown
---
id: DEMO-NOTE-2099-0002
title: DEMO synthetic runbook
owner: DEMO Knowledge Ops
tags:
  - python
  - infra
  - demo
---

Body text. Inline tags like #deployment and #2099 also count.
```

Parser rules:

- Only treat content as frontmatter when the first non-empty line is `---` and a closing `---` exists.
- Support the inline list (`tags: [a, b, c]`) and the block list (`tags:` followed by indented `- value` lines).
- Trim whitespace and surrounding quotes from each tag value.
- Ignore all other frontmatter keys.

### Inline tags

- Match `#tag` tokens in the body where a tag is `#` followed by `[A-Za-z0-9_-]+`.
- Do not match inside fenced code blocks.
- Do not treat Markdown headings (`# Heading`, `## Heading`) as tags — a tag requires a non-space, non-`#` character immediately after a single `#` and must not be at the start of a heading line.
- Normalize matched inline tags to lowercase.

## SQLite Schema Requirements

Create a schema that can support at least:

### `schema_migrations`

- `version integer primary key`
- `applied_at text not null`

### `files`

- `path text primary key`
- `indexed_at text not null`
- `content_hash text not null`

### `file_tags`

- `path text not null`
- `tag text not null`
- a uniqueness constraint on `(path, tag)`

Index behavior:

- New databases should be created at latest schema version.
- Re-indexing a file replaces its `file_tags` rows atomically.

## Required Project Files

If creating from scratch, include:

```text
pyproject.toml
README.md
tag_retriever/__init__.py
tag_retriever/cli.py
tag_retriever/indexer.py
tag_retriever/search.py
tag_retriever/stats.py
tag_retriever/diff.py
tag_retriever/db.py
examples/notes_2099/demo_note_2099_0001.md
examples/notes_2099/demo_note_2099_0002.md
examples/notes_2099/demo_note_2099_0003.md
tests/test_indexer.py
tests/test_search.py
tests/test_stats.py
tests/test_diff.py
tests/test_export.py
tests/test_frontmatter.py
```

You may use a different internal module split if the public CLI behavior and tests are equivalent.

## Testing Requirements

Write at least 12 pytest tests covering:

1. Ingest: indexing a fixture directory inserts files and their tags.
2. Find (AND logic): a multi-tag query returns only files carrying every tag.
3. Find (no match): a query with no matching files prints empty-state and exits `0`.
4. Find (single tag): a single-tag query returns all files carrying that tag.
5. Stats output format: the histogram is a valid Markdown table sorted by count then tag.
6. Diff after re-index: changing a file's tags is reported under `changed` with added/removed tags.
7. Diff with no changes: re-running diff on an unchanged tree reports "no changes" and exits `0`.
8. Export JSON: deterministic array with `file`, `tags`, `indexed_at`, `content_hash`.
9. Export CSV: stable headers and semicolon-joined sorted tags.
10. Frontmatter parsing (YAML inline list): `tags: [a, b, c]` is parsed correctly.
11. Frontmatter parsing (YAML block list): `tags:` with `- a` lines is parsed correctly.
12. Inline `#tag` extraction: body `#tags` are captured, headings and fenced code are not.

## README Requirements

The README should include:

- DEMO-only warning.
- Installation/setup commands.
- Example commands using the provided fixtures.
- Explanation of frontmatter and inline tag formats.
- Explanation of the AND search semantics.
- Statement that the project is local-only and does not call external APIs.

## Acceptance Criteria

The task is complete when:

- `tag-retriever --help` works and lists all subcommands.
- Indexing the example directory inserts files and tags.
- `find` returns AND-matched files sorted by recency.
- `stats` prints a deterministic Markdown histogram table.
- `diff` reports added/removed/changed tags and is read-only.
- `export` produces deterministic JSON and CSV.
- All three frontmatter/inline tag forms parse correctly.
- Tests pass with `pytest` or the project runner.
- README explains usage and DEMO-only safety.
- No real data, real secrets, or real external service calls are present.

## Stretch Requirements for Larger Token-Usage Runs

If the core task is completed quickly, continue with these optional items in order. Stop when the run budget or operator instructions require stopping.

1. Add `tag-retriever find --any "a,b"` for OR semantics in addition to the default AND.
2. Add `--since 2099-MM-DD` and `--until 2099-MM-DD` filters to `find` and `export`.
3. Add `tag-retriever related <tag>` listing tags that co-occur most often with the given tag.
4. Add a `--limit <n>` option to `find` and `stats`.
5. Add golden-file tests for `stats` and JSON `export` output.
6. Add a fixture generator that creates 50 deterministic `DEMO-NOTE-2099-*` files with stable tag sets.
7. Add a data-quality warning for notes with no tags during `index`.
8. Add tests for malformed frontmatter (missing closing `---`).
9. Add tests for tag normalization (mixed case, surrounding quotes).
10. Add a short `docs/DEMO_2099_OPERATOR_NOTES.md` describing the local-only demo.

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
- implemented CLI subcommands;
- any incomplete stretch items;
- confirmation that all examples are synthetic DEMO 2099 data.
