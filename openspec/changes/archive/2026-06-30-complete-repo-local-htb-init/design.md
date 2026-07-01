## Context

AGILE-AI-HTB already has the right split: `htb` is an installed operator command, while local Harness state is configured through `.htb/config.toml`, `.htb/secrets.env`, `.htb/guardrails.yaml`, and SQLite. The sharp edge is first-run truthfulness: `htb init` does not create the DB yet and writes relative to the current directory, even when the operator is inside a Git repo subdirectory.

## Goals / Non-Goals

**Goals:**
- Make `htb init` create the complete local `.htb/` state needed by `htb serve`.
- Keep all Harness state repo-local by default.
- Make default init target the Git repo root when available.
- Prevent accidental Git tracking of `.htb/` local state.
- Preserve existing config, secrets, guardrails, and database contents on repeated init.

**Non-Goals:**
- No global database, daemon, OS config directory, or multi-repo registry.
- No new dependency or setup wizard.
- No change to Worker Adapter auth/model setup.
- No change to runtime setting precedence: CLI flag > environment variable > config > default.

## Decisions

1. **Resolve the default init root before writing default paths.**
   - If Git reports a repository root, default `.htb/` files are written there.
   - Outside Git, default `.htb/` files are written in the current directory.
   - Explicit `--config-path` / `--secrets-path` values remain explicit overrides instead of being silently relocated.
   - Alternative considered: require operators to run from the repo root. Rejected as needless friction.

2. **Create the SQLite DB during `htb init` with existing `db.init_db`.**
   - Use the configured `database_path`, which defaults to `.htb/harness.db`.
   - Existing DBs are migrated/idempotently seeded by the current initializer.
   - Alternative considered: keep lazy DB creation in `htb serve`. Rejected because init should answer “everything needed is here” truthfully.

3. **Use Git-local ignore protection first.**
   - In a Git repo, append `.htb/` to the repo’s local exclude file when missing.
   - This avoids editing the user’s tracked `.gitignore`.
   - Outside Git, write `.htb/.gitignore` with deny-all contents so accidental nested Git usage still keeps local state private.
   - Alternative considered: always edit `.gitignore`. Rejected because it creates tracked project noise for local operator state.

4. **Print the actual initialized root and artifacts.**
   - Output should name the resolved init root plus the files written/verified.
   - This makes subdirectory runs understandable without adding prompts.

## Risks / Trade-offs

- **Risk:** A user expects subdirectory-local `.htb/`. → Mitigate by printing the resolved init root and honoring explicit path flags.
- **Risk:** Git worktrees or unusual `.git` layouts make `.git/info/exclude` path lookup fragile. → Mitigate by using Git’s own path resolution where available and falling back to `.htb/.gitignore`.
- **Risk:** `htb init` now touches the DB. → Mitigate by using the existing idempotent initializer and testing repeated runs preserve data.
