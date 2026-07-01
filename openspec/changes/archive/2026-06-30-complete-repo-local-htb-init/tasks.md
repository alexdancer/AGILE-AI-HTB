## 1. Init Root and Paths

- [x] 1.1 Add a small init-root resolver that uses the Git repository root for default `htb init` paths and falls back to the current directory outside Git.
- [x] 1.2 Update `htb init` so default `.htb/config.toml`, `.htb/secrets.env`, and `.htb/guardrails.yaml` are written under the resolved init root.
- [x] 1.3 Preserve explicit `--config-path` and `--secrets-path` behavior so operator-supplied paths are not silently relocated.

## 2. Complete Local State

- [x] 2.1 Call the existing database initializer during `htb init` using the configured database path, defaulting to `.htb/harness.db`.
- [x] 2.2 Ensure repeated `htb init` preserves existing config values, secret values, guardrails, and database rows while applying missing defaults or migrations.
- [x] 2.3 Update `htb init` output to show the resolved init root and the config, secrets, guardrails, and database paths written or verified.

## 3. Ignore Protection

- [x] 3.1 Add Git ignore protection that appends `.htb/` to the repository-local exclude file when initializing inside a Git repo and the rule is missing.
- [x] 3.2 Add the outside-Git fallback that writes `.htb/.gitignore` with deny-all contents.

## 4. Docs and Tests

- [x] 4.1 Add CLI tests for repo-root init from a subdirectory, outside-Git init, DB creation, idempotent rerun preservation, explicit path overrides, and ignore protection.
- [x] 4.2 Update operator docs to state that installed `htb` is global while `.htb/` state is repo-local and `htb init` creates the SQLite DB.
- [x] 4.3 Run `openspec validate complete-repo-local-htb-init --strict`.
- [x] 4.4 Run targeted CLI/config tests, then `uv run pytest` before marking implementation tasks complete.
