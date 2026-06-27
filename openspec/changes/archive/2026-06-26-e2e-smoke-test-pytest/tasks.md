## 1. Create smoke test

- [x] 1.1 Create `tests/smoke/__init__.py` (empty)
- [x] 1.2 Create `tests/smoke/test_end_to_end.py` with single test: project → task → launch → Worker Run → token ledger → Review
- [x] 1.3 Test uses synthetic data only — no network, no subprocess, no real Worker CLI

## 2. Verify

- [x] 2.1 Run new smoke test in isolation: `pytest tests/smoke/`
- [x] 2.2 Run full pytest suite, verify no regressions
