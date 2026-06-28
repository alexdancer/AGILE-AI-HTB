## Why

Control-plane model setup is still too export-heavy: users can choose Anthropic in the portal, but they still have to know to edit `.htb/secrets.env` or export an API key before the connection works. The portal should be the normal setup path for provider/model/key without collapsing control-plane credentials into Worker Adapter auth.

## What Changes

- Add a portal-managed control-plane API key entry flow on `/settings/control-plane`.
- Store submitted control-plane API key values in ignored `.htb/secrets.env`, never in `.htb/config.toml`.
- Keep provider, model, base URL, and internal env-name settings in `.htb/config.toml`.
- Hide or de-emphasize the API key env-name field behind advanced settings so normal users paste a key instead of managing env vars.
- Preserve existing key values when the API key field is blank.
- Keep connection testing separate from saving and continue redacting secrets from UI, logs, JSON, and test evidence.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `control-plane-model-connection`: control-plane model setup accepts a portal-submitted API key value for local secret storage while preserving the model-layer split from Worker Adapter credentials.
- `operator-setup`: portal-driven operator setup no longer requires users to manually export or edit control-plane API key environment variables for the common local path.

## Impact

- Affected code: control-plane settings route/payload, `control_plane.html`, operator secret file helpers, and portal tests.
- Affected local files: `.htb/config.toml` remains non-secret; `.htb/secrets.env` may be updated by the portal with the selected control-plane secret value.
- No new dependencies, external secret vault, OAuth flow, Worker Adapter auth changes, or provider model discovery.
