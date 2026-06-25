## Context

The portal already has `/settings/control-plane`, but it only displays and tests the startup-resolved `Settings` values. The effective control-plane connection is loaded from env and `.htb/config.toml`, then held in `app.state.settings`; `LLMClient` also holds that settings object. Estimation, task breakdown, and agent review use control-plane models, while Worker Adapter model selection remains separate.

## Goals / Non-Goals

**Goals:**
- Let operators change control-plane provider/model settings from the portal without restarting.
- Persist non-secret connection choices to `.htb/config.toml` before applying them live.
- Keep API key values out of portal forms and `.htb/config.toml`.
- Make the default harness model choice affect estimation and task breakdown unless the operator opts out.
- Mark connection evidence stale after config changes so setup does not present an old test as valid.

**Non-Goals:**
- No live provider model discovery/catalog fetching.
- No Worker Adapter model selection changes.
- No secret-manager UI or stored API key values.
- No in-flight request coordination; the new settings apply to subsequent control-plane requests.

## Decisions

### 1. Persist first, then hot-swap runtime state

Saving the form rewrites `.htb/config.toml` first. Only after that succeeds does the route replace `app.state.settings` and `app.state.llm_client`.

Alternative considered: hot-swap first, then write config. Rejected because it can leave a hidden runtime-only model choice that disappears on restart.

### 2. Keep `.htb/config.toml` as the source of truth

The portal edits the same non-secret operator config used by `htb init`, `htb serve`, and `Settings`. SQLite remains for operational status/evidence, not core non-secret config.

Alternative considered: store portal-selected model settings in `portal_settings`. Rejected because it splits the control-plane model source across DB and TOML.

### 3. Use tiny presets plus free-text advanced fields

The page exposes presets for:
- OpenAI: `gpt-5.4-mini`
- Anthropic: `claude-haiku-4-5`
- OpenAI-compatible: custom model plus base URL

Presets fill provider/model/base URL shape, while advanced fields remain editable for exact model IDs, custom base URLs, and env names.

Alternative considered: fetch provider model catalogs. Rejected as stale-prone and out of scope for the first useful slice.

### 4. One control-plane API key env name by default

The default remains `AGILE_AI_HTB_CONTROL_API_KEY`. The env-name field is editable so operators can point at `ANTHROPIC_API_KEY` or another existing env var if desired. The portal never accepts raw API key values.

### 5. Default coupled estimator/breakdown update with opt-out

The save form includes a default-checked option to apply the selected model to `estimator_model` and `task_breakdown_model`. If unchecked, existing split-model values remain unchanged.

This preserves advanced control-plane split-model use without making the normal harness model choice feel broken.

### 6. Stale status instead of auto-test

Saving does not call the provider. It records or updates `control_plane_model` backend status as offline/untested with a sanitized detail such as `configuration changed; test required`. The explicit Test button remains the proof step.

## Risks / Trade-offs

- [Risk] Environment variables still override `.htb/config.toml`, so a portal save may not become effective if `AGILE_AI_HTB_CONTROL_MODEL` or related env vars are set. → Mitigate by showing effective-vs-configured values or rejecting/labeling saves shadowed by env overrides.
- [Risk] `.htb/secrets.env` edits can race manual edits. → Mitigate with small append/update helper preserving existing values and only adding placeholders for missing env names.
- [Risk] Existing test evidence may look current after model changes. → Mitigate by explicitly marking status `needs test` on every saved config change.
- [Risk] In-flight control-plane calls can complete under the old model. → Accept; product promise is next-request semantics.
