## Why

The Control Plane settings page currently labels the model field like a dropdown, but renders it as a free-text `<input>` with a `datalist`. In practice this behaves like a textbox with weak browser-specific suggestions, so operators do not get an obvious model dropdown when choosing the harness's own control-plane/orchestrator model.

## What Changes

- Replace the Control Plane model textbox/datalist UX with an actual model dropdown for the small curated model set.
- Keep Control Plane model selection separate from Worker Adapter model inventories and launch model choices.
- Preserve a custom model entry path for OpenAI-compatible or future provider/model IDs without turning the normal path into free text.
- Keep existing save behavior: non-secret settings persist to `.htb/config.toml`, submitted secrets stay out of config/status/UI, runtime settings hot-swap for subsequent Control Plane requests, and prior connection evidence is marked `needs_test` after save.
- Update portal tests so the expected UI contract is a real `<select>`/dropdown rather than a `datalist` textbox.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `control-plane-model-connection`: Require the portal's normal Control Plane model choice to use a real dropdown for curated models while preserving a custom model path for OpenAI-compatible or future IDs.

## Impact

- Affected UI: `src/agile_ai_htb/templates/control_plane.html`
- Affected route/context if needed: `src/agile_ai_htb/routes/portal.py`
- Affected tests: `tests/portal/test_control_plane.py`
- No database migration, new dependency, Worker Adapter model discovery change, or API contract change is expected.
