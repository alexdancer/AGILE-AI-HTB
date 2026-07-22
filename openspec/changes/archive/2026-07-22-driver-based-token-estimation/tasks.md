## 1. Coefficients and arithmetic

- [x] 1.1 Add `data/estimation_coefficients.json`: per-Worker-Adapter/per-model factor blocks plus a `default` block; each factor tagged `seed` or `fitted(n)`. `p` (output/turn) and turn factors `fitted(n)` from recorded demo runs; `a`, `b`, `g`, `k` as `seed` (`g` explicitly seed — cannot be fitted while `demo_worker.py` pins cache to zero).
- [x] 1.2 Add `estimation_coefficients.py`: load + validate the file, resolve `(adapter, model) → coefficients` with `default` fallback, and compute `Ê = T·(a·r + b·m) + (g/2)·T(T−1) + p·T + k·τ` returning the estimate plus the per-factor provenance used.
- [x] 1.3 Add a deterministic self-check (`assert`-based `__main__`/`test_`) pinning known drivers + coefficients to an expected `Ê`, so an equation or coefficient regression fails loudly.

## 2. Estimator contract

- [x] 2.1 Change `EstimateResult`: `token_estimate` becomes the computed value; add `drivers` (`files_to_read`, `files_to_modify`, `expected_turns`, `needs_test_run`), `shadow_token_estimate`, `estimate_disagreement`; `source = "driver_arithmetic"`. Update `as_dict()`.
- [x] 2.2 Update `_system_prompt`: request Estimation Drivers + a `shadow_token_estimate` (LLM's own guess) instead of an owned primary estimate; keep the no-Worker-model rule and existing project/calibration context.
- [x] 2.3 Update `_validate_result`: require and type-check the driver fields + `shadow_token_estimate`; reject a top-level owned final estimate; compute `token_estimate` via `estimation_coefficients.py` and set `estimate_disagreement = |Ê − shadow| / Ê`.
- [x] 2.4 Preserve fallback: LLM failure or invalid/missing drivers still raises `EstimatorError` → manual-estimate-only; no coefficient path runs without valid drivers; missing coefficients resolve to `default` (not a failure).

## 3. Persistence and consumer

- [x] 3.1 In `routes/tasks.py`, persist `drivers`, `shadow_token_estimate`, and `estimate_disagreement` in task metadata; leave `estimate_tokens=result.token_estimate` and `route_worker_model(estimate_tokens=...)` unchanged.

## 4. Tests and docs

- [x] 4.1 Move the estimator evals + golden decomposition fixtures to the drivers contract: assert emitted drivers, the harness-computed estimate, its provenance tags, and the shadow/disagreement; drop assertions that the LLM owns the integer.
- [x] 4.2 Add tests for coefficient resolution (`default` fallback), the arithmetic on a fixed driver set, and disagreement computation.
- [x] 4.3 Confirm `docs/adr/0004` stays accurate; note in `CONTEXT.md` that `token_estimate` is now driver-computed with a persisted shadow.
- [x] 4.4 Run `openspec validate driver-based-token-estimation --strict`, `openspec validate --all --strict`, `uv run pytest`, and `npm run check`.
