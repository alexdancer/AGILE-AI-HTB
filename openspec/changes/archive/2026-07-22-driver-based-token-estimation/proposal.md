## Why

`estimation.py` asks the Estimator LLM to emit a raw `token_estimate` integer directly — the one thing an LLM is worst at, since it has no way to know a given adapter's per-turn context cost. The number is unexplainable (nothing on the card justifies it), unfalsifiable (a wrong value gives no reason why), and un-tunable (a point estimate offers no parameter for run history to update). Meanwhile the harness already records, per turn, exactly the data an equation needs (`fresh_input`, `cache_read`, `cache_write`, `output`, `reasoning`, `turn_count` via `evidence_reporting.py`), and the LLM *is* good at the qualitative drivers — how many files, how many turns, does it need a test run. This change implements the decision in `docs/adr/0004-driver-based-token-estimation.md` (first slice).

## What Changes

- The Estimator LLM emits structural **Estimation Drivers** — `files_to_read`, `files_to_modify`, `expected_turns`, `needs_test_run` (plus the existing `complexity`, `confidence`) — instead of owning the token magnitude.
- The harness computes `token_estimate` **arithmetically** from per-Worker-Adapter, per-model **coefficients** using the ADR-0004 equation `Ê = T·(a·r + b·m) + (g/2)·T(T−1) + p·T + k·τ`. The computed value keeps the name `token_estimate`, so `route_worker_model`, the board card, and stored `estimate_tokens` are unchanged.
- Coefficients ship as a **checked-in, provenance-tagged file** (`data/estimation_coefficients.json`); each factor is labelled `seed` or `fitted(n)`. `g` (context-growth/cache-dominated) ships as an honest `seed` because `demo_worker.py` pins cache to zero and it cannot be fitted from the demo. A `default` block guarantees every adapter/model resolves.
- The LLM's own guess is retained as a **shadow** (`shadow_token_estimate`) with `estimate_disagreement = |computed − shadow| / computed` persisted in task metadata as a quality signal.
- Driver arithmetic is the **primary** path: an Estimator LLM failure or invalid/missing drivers yields no automatic estimate (manual estimate only) — the existing "never silently substitute a heuristic" rule is preserved.

## Capabilities

### New Capabilities
- `driver-based-estimation`: the Estimator emits Estimation Drivers + a shadow guess; the harness computes `token_estimate` from a checked-in, provenance-tagged, per-adapter/per-model coefficient set; disagreement is persisted; failures fall back to manual estimate only.

### Modified Capabilities
- `estimator-project-context`: the estimator output contract changes from a primary `token_estimate` to Estimation Drivers plus a shadow guess; it still excludes Worker model choice and still receives project + calibration context.
- `estimator-task-decomposition-evals`: golden decomposition fixtures and estimator evals assert emitted drivers and the harness-computed estimate (and its shadow) rather than a raw LLM integer.

## Impact

- Backend: `estimation.py` (`EstimateResult` fields, system prompt, `_validate_result`); new `estimation_coefficients.py` (loader + equation) reading `data/estimation_coefficients.json`; `routes/tasks.py` (persist `drivers` + `shadow_token_estimate` + `estimate_disagreement` in metadata; `token_estimate`/routing line unchanged).
- Tests: 28 estimator evals + golden decomposition fixtures move to the drivers contract; add a coefficient-arithmetic self-check.
- Non-goals: no change to `estimation_calibration.py` (the prompt-example/band-check layer stays beside, untouched); no auto-fitting loop from completed runs; no DB-backed/runtime-mutable coefficients; no p50/p90 estimate bands; no reserved-budget headroom; no change to `route_worker_model` or `adapter-aware-model-routing`.
