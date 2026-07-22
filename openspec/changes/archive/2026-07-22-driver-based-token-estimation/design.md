## Context

`estimate_task()` (`estimation.py`) sends one `temperature=0`, `json_object` request and validates a strict 8-field `EstimateResult` whose primary field is a raw LLM `token_estimate: int`. The only consumer is `routes/tasks.py` (~L347-378): it passes `result.token_estimate` to `route_worker_model(estimate_tokens=...)`, stores it as `estimate_tokens`, and returns `result.as_dict()` for the card. The actual-side decomposition the equation needs already lands via `evidence_reporting.py` (`fresh_input`/`cache_read`/`cache_write`/`output`/`reasoning` + `turn_count`). A separate reference-class layer (`estimation_calibration.py`, ~380 LOC) already injects example cases + band checks into the prompt. Motivation, the equation, and alternatives are in `docs/adr/0004`.

## Goals / Non-Goals

**Goals:**
- LLM emits Estimation Drivers; harness computes `token_estimate` arithmetically from checked-in per-adapter/per-model coefficients.
- Keep the computed value named `token_estimate` so routing, the card, and stored `estimate_tokens` need no change.
- Persist the LLM's guess as a shadow with a disagreement metric as a quality signal.
- Preserve manual-estimate-only fallback with no heuristic substitution.

**Non-Goals:**
- No change to `estimation_calibration.py` (prompt-example nudge + band checks stay beside).
- No auto-fitting loop, no DB-backed/mutable coefficients, no p50/p90 bands, no reserved-budget headroom (later ADR-0004/0002 layers).
- No change to `route_worker_model` behavior or `adapter-aware-model-routing`.

## Decisions

- **`token_estimate` is the computed value; drivers + shadow are additive.** `EstimateResult` gains `drivers: {files_to_read, files_to_modify, expected_turns, needs_test_run}`, `shadow_token_estimate: int`, `estimate_disagreement: float`; `token_estimate` now holds `Ê`. `source` becomes `driver_arithmetic`. *Alternative — rename to `computed_token_estimate`:* rejected, it churns routing/card/storage for no behavioral gain.
- **The LLM stops guessing the magnitude as the answer but still emits it as a shadow.** The prompt requests drivers + a `shadow_token_estimate`; validation requires the driver fields and rejects a top-level owned estimate. Disagreement `d = |Ê − E_llm| / Ê` is stored in task metadata (no schema/migration). *Alternative — a real DB column for the shadow:* rejected for this slice; metadata is sufficient to observe disagreement.
- **Equation lives in a small `estimation_coefficients.py`.** It loads `data/estimation_coefficients.json` and evaluates `Ê = T·(a·r + b·m) + (g/2)·T(T−1) + p·T + k·τ`, keeping `estimation.py` focused on prompt/validation. A `default` coefficient block resolves any adapter/model with no specific entry (this is not an LLM failure). *Alternative — inline the arithmetic in `estimation.py`:* acceptable but the loader + provenance tags earn their own module.
- **Coefficients are checked-in and provenance-tagged.** Each factor carries `seed` or `fitted(n)`; `p` and turn count are `fitted(n)` from recorded demo runs, `g`/`a`/`b`/`k` ship as `seed`. The harness never fabricates cache-bearing demo evidence to make `g` look fitted. *Alternative — DB rows updated by runs:* deferred; matches the ADR's "replaced by the first real Worker Run" as a later layer.
- **Fallback unchanged.** Estimator LLM failure or invalid/missing drivers raises `EstimatorError` → `Estimated` + `requires_manual_estimate`, exactly as today. No coefficient path runs without valid drivers.

## Risks / Trade-offs

- **Contract change touches all 28 estimator evals + golden fixtures** → they move in this change; the arithmetic gets a deterministic self-check so a coefficient/equation regression fails loudly.
- **Seed `g` may be materially wrong until a real cache-bearing run lands** → labelled `seed` on the card provenance and in the file; correcting it is a data edit, not a code change. The disagreement metric surfaces gross mismatch immediately.
- **Two influences on the number (arithmetic sets it, calibration examples nudge the shadow)** → acceptable and intended; the shadow is explicitly non-authoritative and only measured against the computed value.

## Migration Plan

1. Add `estimation_coefficients.py` + `data/estimation_coefficients.json` (seed + fitted factors, `default` block).
2. Change `EstimateResult`, the system prompt, and `_validate_result` to the drivers + shadow contract; compute `token_estimate` from the coefficient module.
3. Persist `drivers` + `shadow_token_estimate` + `estimate_disagreement` in task metadata in `routes/tasks.py`; leave the `estimate_tokens`/routing line untouched.
4. Move estimator evals + golden fixtures to the drivers contract; add the arithmetic self-check.
Rollback is reverting the change; no data migration (shadow/disagreement are additive metadata).

## Open Questions

- None blocking. Shadow + disagreement live in task metadata for this slice; promote to a column only if accuracy tracking later needs to query them directly.
