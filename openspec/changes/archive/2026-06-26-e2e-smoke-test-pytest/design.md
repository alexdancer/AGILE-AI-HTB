## Context

`scripts/local_runner_smoke.py` proves the full governance loop works: DB init → project connect → worker adapter → task create → launch → Worker Run → token ledger → task moves to Review. But it runs as a standalone script, not via `pytest`. No automated CI can verify the governance loop. Existing tests use synthetic data and fake LLM clients — those patterns work for the smoke test too.

## Goals / Non-Goals

**Goals:**
- One pytest test in `tests/smoke/` that mirrors the smoke script's governance loop
- Uses synthetic data only (zero network, zero real Worker CLI)
- Verifies: task created → launched → Worker Run exists → token turns recorded → task status is Review
- Reuses existing `Settings` + `TestClient` + `db` patterns from other tests

**Non-Goals:**
- Testing real Worker Adapter CLI execution
- Verifying proxy-governed or native-usage tracking modes
- Multi-project or cross-project scenarios
- Porting every scenario from the smoke script

## Decisions

### 1. Single test, single scenario

One test function covers the happy-path governance loop. The existing smoke script has multiple scenarios — this test picks the most representative one (create task → launch → verify).

**Alternative considered:** Separate test per scenario → rejected. One test proves the loop works; additional smoke scenarios can be added later when this one catches a regression.

### 2. Synthetic tokens via direct DB writes

The smoke test writes synthetic `token_turns` rows directly to simulate Worker token usage, matching the existing fake test patterns. No real LLM calls.

### 3. File location: `tests/smoke/test_end_to_end.py`

New directory `tests/smoke/` under the existing test root. Follows the domain-folder convention established in the test reorg.

## Risks / Trade-offs

- **[Risk] Smoke test may be slow if it launches a real subprocess** → Mitigation: No subprocess launch. The test simulates launch by directly calling `db.create_worker_run()` and `db.record_token_turn()`, then `refresh_task_from_session()` to move the task to Review.
