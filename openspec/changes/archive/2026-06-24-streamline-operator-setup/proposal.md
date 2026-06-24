## Why

Local and hosted operators currently need to stitch together several environment variables, CLI flags, and runbook steps before AGILE-AI-HTB can estimate, launch, and verify work. That setup burden hides the important model-layer boundary: the control-plane model uses AGILE-AI-HTB provider credentials, while Worker harness models use their own CLI/auth and adapter verification.

## What Changes

- Add a first-class operator setup flow via `htb init` that writes local non-secret configuration for the harness.
- Make `htb serve` load operator configuration by default while preserving override precedence: CLI flag > environment variable > config file > built-in default.
- Add `htb check` to report setup readiness with `PASS`, `WARN`, and `FAIL` lines for config, required secrets, control-plane reachability, Local Runner state, and Worker Adapter readiness.
- Update local setup and runbook documentation to prefer the operator setup path over export-heavy startup snippets.
- Keep demo data seeding separate from real operator setup; demos may use the same setup flow with demo-safe values but should not own the product model.

## Capabilities

### New Capabilities
- `operator-setup`: Operator initialization, persisted non-secret harness configuration, configuration precedence, and readiness checking.

### Modified Capabilities

None.

## Impact

- CLI: `src/agile_ai_htb/cli.py`
- Settings/config loading: `src/agile_ai_htb/settings.py` and any small helper needed for `.htb/config.toml`
- Existing health/control-plane/Worker Adapter routes reused by readiness checks where practical
- Docs/runbooks: README and local demo/operator proof docs that currently list manual exports
- Tests: CLI entrypoint/config precedence/readiness output tests
- Dependencies: no new runtime dependency; use Python standard library TOML parsing where available
