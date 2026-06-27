## Why

`scripts/local_runner_smoke.py` exists as a standalone smoke script that proves the full governance loop end-to-end: DB init → project connect → worker adapter setup → task create → launch → Worker Run evidence → token ledger → review. But it's not run by `pytest`, so regressions are only caught manually. Porting the smoke to pytest means CI can verify the governance loop on every push.

## What Changes

- Create `tests/smoke/test_end_to_end.py` with a single pytest test that mirrors `scripts/local_runner_smoke.py`
- Use the existing fake/synthetic patterns from other tests (no network calls, no real Worker CLI)
- Initialize DB, create connected project, seed worker adapter, create task, simulate launch, verify Worker Run record exists, verify token turns recorded, verify task moved to Review
- Keep it bounded: one test, one scenario, ~80 lines

## Capabilities

### New Capabilities

- `e2e-governance-smoke`: A pytest-based smoke test SHALL verify the full governance loop (project → task → launch → Worker Run → token ledger → Review) using synthetic data with zero external dependencies.

### Modified Capabilities

None. Additive only.

## Impact

- `tests/smoke/test_end_to_end.py`: New test file (~80 lines, single test function)
- No source code changes
