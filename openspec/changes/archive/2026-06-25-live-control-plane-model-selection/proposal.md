## Why

Operators can configure the AGILE-AI-HTB control-plane model only through environment/config startup settings today. That makes model choice harder than it needs to be and makes the portal's "Control plane model" page read-only even though model choice is core harness setup.

## What Changes

- Add a portal control-plane connection editor that lets an authenticated operator choose provider, model, base URL, and API key env name.
- Provide a tiny preset set for common choices while preserving advanced free-text fields:
  - OpenAI: `gpt-5.4-mini`
  - Anthropic: `claude-haiku-4-5`
  - OpenAI-compatible: custom model plus base URL
- Persist non-secret choices to `.htb/config.toml`; never store API key values in the portal form or config file.
- Apply saved control-plane settings live for subsequent control-plane requests by replacing the running settings/client after the config write succeeds.
- Keep the control-plane model separate from Worker Harness model selection and Worker Adapter discovered/allowed models.
- Default to applying the selected model to estimator and task-breakdown model settings, with an opt-out for advanced split-model operation.
- Mark the previous control-plane connection test as stale/needs test after a save; testing remains an explicit operator action.
- If the configured API key env name changes, ensure `.htb/secrets.env` has a placeholder entry rather than accepting secrets through the portal.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `control-plane-model-connection`: Add live portal editing and stale-test behavior for the control-plane provider/model connection.
- `operator-setup`: Persist portal-edited non-secret control-plane settings to `.htb/config.toml` and placeholder-only secret env guidance to `.htb/secrets.env`.

## Impact

- Affected UI: `src/agile_ai_htb/templates/control_plane.html`, setup status display.
- Affected routes: `src/agile_ai_htb/routes/portal.py` control-plane settings endpoints.
- Affected config helpers: `src/agile_ai_htb/operator_config.py`, `src/agile_ai_htb/settings.py` usage only as needed.
- Affected runtime state: `app.state.settings` and `app.state.llm_client` hot-swap after successful config write.
- Affected docs/tests: control-plane settings route tests, operator config helper tests, local setup/runbook references if they describe restart-only model changes.
