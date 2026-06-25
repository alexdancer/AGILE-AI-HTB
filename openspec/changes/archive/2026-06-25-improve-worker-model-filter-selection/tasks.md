## 1. Worker Setup UI

- [x] 1.1 Update `src/agile_ai_htb/templates/workers.html` to add a discovered-model filter input beside the allowed model checkbox list.
- [x] 1.2 Add `Check visible` and `Uncheck visible` buttons that only toggle currently visible discovered model checkboxes.
- [x] 1.3 Keep checkbox names as `allowed_models` so the existing save route and validation contract remain unchanged.
- [x] 1.4 Keep the no-JavaScript fallback as the current visible checkbox list.

## 2. Tests and Verification

- [x] 2.1 Update portal tests to assert the Worker Setup page renders the filter input and visible bulk action controls after model discovery.
- [x] 2.2 Keep/extend allowed-model route tests to verify only discovered submitted model IDs are saved and invalid IDs are rejected.
- [x] 2.3 Run targeted portal tests for Worker Setup model discovery/allowed selection.
- [x] 2.4 Run the project verification command `pytest` if targeted tests pass.
