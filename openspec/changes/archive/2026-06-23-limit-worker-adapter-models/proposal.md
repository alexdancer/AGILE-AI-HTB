## Why

Worker model discovery can return more models than an operator wants the AGILE board to recommend or launch. Operators need a simple allow-list after discovery so estimates and manual board launches stay inside approved Worker models, without changing the separate control-plane estimator model.

## What Changes

- Add an operator-selected allowed Worker model subset after native model discovery.
- Constrain estimator Worker recommendations to the selected allowed models for the active/default Worker Adapter.
- Show only allowed models in the AGILE board launch model dropdown.
- Block launch attempts that name a model outside the adapter's allowed subset.
- Treat an empty allowed subset as setup-incomplete / not launchable.
- Keep tracking modes (`proxy_governed`, `native_usage`, `observed_only`) separate from adapter identity and model allow-listing.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `native-worker-model-discovery`: Discovery must preserve the discovered model evidence while allowing the operator to choose the subset allowed for governed use.
- `guided-worker-setup`: Worker setup must expose the allowed-model selection after discovery.
- `board-launch-selection`: The AGILE board must only present allowed Worker models for manual launch.
- `governed-worker-launch`: Launch guardrails must reject models outside the adapter's allowed subset.

## Impact

- Worker setup route/template for allowed-model selection.
- Worker adapter persistence semantics around discovered models vs allowed models.
- Estimation recommendation constraint logic in task creation.
- AGILE board launch dropdown and launch guardrails.
- Tests for discovery preservation, allowed subset persistence, recommendation constraint, board options, and launch rejection.
