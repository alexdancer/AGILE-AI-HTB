## Why

OpenCode and similar Worker Adapters can discover long model lists, and the current allowed-model checkbox wall makes selecting a small approved subset tedious. Operators need a faster way to narrow the discovered list without changing the underlying Worker model allow-list contract.

## What Changes

- Add a client-side filter to the discovered Worker model selector on Worker Setup.
- Add "Check visible" and "Uncheck visible" controls that apply only to currently filtered/visible discovered model checkboxes.
- Keep the saved allowed Worker model subset in the existing adapter supported-models/allowed-model path.
- Keep backend validation that submitted allowed models must come from the discovered Worker model inventory.
- Do not add provider presets, fuzzy allow rules, or new Worker Adapter persistence.

## Capabilities

### New Capabilities

### Modified Capabilities
- `guided-worker-setup`: Worker Setup model selection becomes filterable and supports bulk visible check/uncheck.
- `native-worker-model-discovery`: Discovered model inventory remains separate from the operator-approved allowed subset while improving allow-list selection UX.

## Impact

- Affected UI: `src/agile_ai_htb/templates/workers.html` discovered-model allowed selection area.
- Affected routes: likely none; `/settings/workers/{adapter_id}/allowed-models` should keep receiving `allowed_models` checkbox values.
- Affected tests: portal rendering/interaction coverage for the filter controls and unchanged allowed-model save behavior.
- Dependencies: none.
