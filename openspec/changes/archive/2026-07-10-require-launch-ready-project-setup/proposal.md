## Why

The Setup Overview can currently claim `Ready to launch` after Control Plane, Token Budget, and Worker Adapter setup even when no Connected Project can launch governed work. This contradicts Project Capability and Setup Overview contracts, sending operators to a board that has no launch-ready execution target.

## What Changes

- Require at least one Connected Project with `launch_ready` capability before Setup Overview reports overall launch readiness.
- Treat no project, unavailable Local Runner, analysis-only projects, and blocked projects as incomplete launch setup; persisted capability alone cannot establish current launch readiness.
- Direct the next setup action to Project Settings when no launch-ready project exists.
- Preserve existing Control Plane, Token Budget, and Worker Adapter readiness checks and their current priority.
- Add focused Portal tests for no-project, disabled-Local-Runner/stale-capability, defensively projected analysis-only, blocked-project, and launch-ready-project states.
- Keep this as a server-rendered truthfulness fix; React Setup migration, schema changes, Worker launch behavior, and Project Capability calculation are out of scope.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guided-worker-setup`: Overall Setup readiness and next-action behavior must include launch-ready Connected Project capability.

## Impact

- Setup state assembly in `src/agile_ai_htb/routes/portal.py`.
- Existing Setup copy in `src/agile_ai_htb/templates/setup.html` only if needed to distinguish missing project capability.
- Focused Portal coverage in `tests/portal/test_setup.py` and related shared helpers.
- No database migration, public API change, dependency change, React implementation, or Worker Adapter behavior change.
