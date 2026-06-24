## 1. Configuration Loading

- [x] 1.1 Add a small operator config loader for `.htb/config.toml` using stdlib `tomllib` and deterministic text writing for init output.
- [x] 1.2 Wire settings resolution so config values participate in precedence `CLI flag > environment variable > .htb/config.toml > built-in default`.
- [x] 1.3 Add tests for config loading, missing config fallback, and env-over-config precedence.

## 2. CLI Commands

- [x] 2.1 Add `htb init` to create `.htb/config.toml` with non-secret local defaults, write `.htb/secrets.env`, and print secret-file edit guidance.
- [x] 2.2 Add `htb check` to report `PASS`, `WARN`, and `FAIL` readiness lines without printing secret values.
- [x] 2.3 Update `htb serve` to use configured defaults for host, port, database path, guardrails path, control-plane model/provider, control-plane API key env name, portal token env name, and Local Runner enablement.
- [x] 2.4 Add CLI tests for `init`, `check`, and `serve` config behavior.

## 3. Readiness Signals

- [x] 3.1 Check required configured env vars by name and fail clearly when missing.
- [x] 3.2 Reuse existing control-plane test logic where practical to report provider/model reachability.
- [x] 3.3 Report Worker Adapter identity separately from tracking mode and warn when only `observed_only` evidence is available.

## 4. Documentation and Verification

- [x] 4.1 Update README/local runbooks to prefer `htb init`, editing `.htb/secrets.env`, `htb serve`, and `htb check` over export-heavy setup snippets.
- [x] 4.2 Keep demo seeding documented as optional follow-up, not the primary setup path.
- [x] 4.3 Run targeted CLI tests and the full pytest suite.
