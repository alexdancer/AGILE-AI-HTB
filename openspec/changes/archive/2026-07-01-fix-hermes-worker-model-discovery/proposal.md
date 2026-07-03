## Why

Hermes Worker Adapter model discovery currently falls through to the generic `{command} models` path, but the installed Hermes CLI has no `models` subcommand. That makes the Worker Setup path report no discovered Hermes models even though Hermes already has model config and seeded Worker model defaults.

## What Changes

- Treat Hermes like other CLIs without a reliable native model-list command: use a curated Hermes Worker model inventory instead of invoking `hermes models`.
- Keep Hermes discovery separate from Hermes launch/verification behavior; discovery only populates selectable Worker model IDs.
- Preserve the existing discovered-vs-allowed model boundary: curated discovery refreshes inventory but does not silently approve models for governed launch.
- Keep OpenCode native discovery unchanged.
- Do not parse Hermes private profile cache/config files for the first slice.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `native-worker-model-discovery`: add Hermes curated model discovery for the Hermes Worker Adapter when native CLI model discovery is unavailable.

## Impact

- Affected code: `src/agile_ai_htb/worker_adapters.py`, `src/agile_ai_htb/worker_model_allowlist.py` if seeded Hermes model IDs need adjustment, and Worker Setup tests under `tests/workers/` and `tests/portal/`.
- Affected behavior: `/settings/workers/{adapter_id}/discover-models` for `adapter_id=hermes` should return curated model IDs and preserve operator-approved allowed models.
- No database schema change, new dependency, new Hermes CLI command, or Worker tracking-mode change.
