## Why

Operators should be able to install `htb` once, enter a repo, run `htb init`, and know the repo now has everything needed for local AGILE-AI-HTB state. Today `htb init` writes config/secrets/guardrails in the current directory, but the database is created later by `htb serve`, and running from a repo subdirectory can create `.htb/` in the wrong place.

## What Changes

- Make `htb init` initialize the Git repository root when run anywhere inside a Git repo; outside Git, keep using the current directory.
- Make `htb init` create or migrate the configured SQLite database immediately, using the existing `.htb/harness.db` default.
- Make `htb init` protect local `.htb/` state from Git tracking without requiring the operator to edit ignore rules by hand.
- Keep installed `htb` as the global command while all Harness state remains repo-local under `.htb/`.
- Preserve existing `.htb/config.toml`, `.htb/secrets.env`, `.htb/guardrails.yaml`, and `.htb/harness.db` values/data on repeated `htb init` runs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `operator-setup`: Tighten `htb init` so it creates complete repo-local Harness state, targets the Git repo root when available, and protects `.htb/` from accidental Git tracking.

## Impact

- CLI init flow: `src/agile_ai_htb/cli.py`
- Operator config helpers: `src/agile_ai_htb/operator_config.py` or a small adjacent helper if needed
- Database initialization: reuse `src/agile_ai_htb/db.py::init_db`
- Docs: README / install / getting-started text that describes what `htb init` creates
- Tests: CLI init tests for repo root detection, DB creation, idempotence, and ignore protection
- Dependencies: none; use standard library and existing DB initialization
