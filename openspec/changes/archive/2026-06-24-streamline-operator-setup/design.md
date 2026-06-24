## Context

AGILE-AI-HTB currently accepts most local setup through environment variables and CLI flags. That is flexible but noisy for normal operators: the portal token, database path, control-plane model, control-plane API key env name, and Local Runner flag are scattered across README snippets and runbooks.

The product also has two model layers that setup must keep separate:

```text
Control-plane model
  estimates, task breakdown, reports, recommendations
  configured by AGILE-AI-HTB settings and API key env

Worker harness models
  OpenCode / Claude Code / Codex / Hermes CLI auth and models
  discovered and verified by Worker Adapters
```

## Goals / Non-Goals

**Goals:**
- Provide one real operator initialization path, not a demo-only shortcut.
- Persist non-secret harness defaults in a small repo-local config file.
- Let `htb serve` work from saved config without repeated exports.
- Add a readiness command that tells operators what is ready, missing, or diagnostic-only.
- Preserve the model-layer boundary and Worker Adapter tracking-mode semantics.

**Non-Goals:**
- No secret vault or keychain integration.
- No general-purpose `.env` loader or new runtime dependency; the setup flow only parses the generated `.htb/secrets.env` file for configured local harness secrets.
- No multi-profile environment manager.
- No setup wizard UI.
- No change to Worker Adapter launch semantics, model routing, or tracking modes.

## Decisions

1. **Use `.htb/config.toml` for non-secret local configuration.**
   - Store values such as database path, guardrails path, host, port, portal token env name, control-plane provider/model, control-plane API key env name, and Local Runner enabled.
   - Do not store raw API keys or passwords.
   - Alternative considered: `.env`. Rejected because it mixes secrets and non-secrets and still requires shell sourcing.

2. **Use stdlib TOML support only.**
   - Python 3.11 includes `tomllib` for reading TOML.
   - Writing the small config file can be deterministic text output; no TOML writer dependency is needed.
   - Alternative considered: add a TOML package. Rejected as unnecessary dependency weight.

3. **Keep override precedence explicit.**
   - Runtime resolution order is: CLI flag > environment variable > `.htb/config.toml` > built-in default.
   - This keeps Render/Docker/env-driven deployments working while improving local defaults.

4. **Make `htb init` boring and safe.**
   - Generate or request only non-secret settings.
   - Write local secret values to `.htb/secrets.env`, keep placeholders for missing provider keys, and print edit guidance without echoing secret values.
   - Default local values should be useful for real local operation, not only synthetic demos.

5. **Make `htb check` a readiness reporter, not a mutator.**
   - It prints `PASS`, `WARN`, or `FAIL` lines and exits nonzero only for hard failures that make the harness unusable.
   - Worker Adapter diagnostics distinguish adapter identity from tracking mode: `proxy_governed`, `native_usage`, and `observed_only`.
   - `observed_only` remains diagnostic-only, not a board-launchable success state.

## Risks / Trade-offs

- **Risk:** Config and environment resolution become confusing. → Mitigate by documenting and testing the single precedence rule.
- **Risk:** Operators think Worker CLI auth comes from the control-plane API key. → Mitigate with `htb check` wording and docs that separate control-plane and Worker harness auth.
- **Risk:** Storing generated portal tokens in config would create a secret file. → Mitigate by storing only env var names in config and writing secret values to ignored `.htb/secrets.env`.
- **Risk:** Readiness checks could become a second implementation of existing routes. → Mitigate by reusing existing settings/control-plane/adapter logic where practical and keeping checks shallow.
