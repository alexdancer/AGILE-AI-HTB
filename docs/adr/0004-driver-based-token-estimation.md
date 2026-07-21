# ADR-0004: Driver-based token estimation with fitted coefficients

**Date**: 2026-07-20
**Status**: accepted

## Context

`estimation.py` asks a single-shot LLM (`temperature=0`, `json_object`) to emit a raw `token_estimate` integer directly. Predicting an absolute token magnitude is the one thing an LLM is worst at — the model has no way to know a given adapter's per-turn context cost, so "47,000" is essentially confabulated. The number is unexplainable (nothing on the card justifies it), unfalsifiable (when it is wrong you cannot tell why), and un-tunable (a point estimate offers no parameter for run history to update, so feedback could only be injected as prompt examples with no way to measure whether it helped — which is why a naive "learn from completed runs" approach was rejected).

Meanwhile the harness already records, per turn, exactly the data an equation needs: `evidence_reporting.py` decomposes each turn's usage into `fresh_input`, `cache_read`, `cache_write`, `output`, `reasoning` with a `turn_count`. Agentic spend is roughly `Σ_turns (context_so_far + output_this_turn)`; context re-accumulates every turn, `cache_read` dominates real logs, and cost grows non-linearly in turns rather than linearly in task size. The LLM *is* good at the qualitative drivers — how many files, how many turns, does it need a test run — which are enumeration and classification.

## Decision

We will have the Estimator LLM emit structural **Estimation Drivers** (files to read, files to modify, expected turns, needs-test-run, complexity, confidence) instead of the token number, and compute the estimate arithmetically from per-Worker-Adapter, per-model **coefficients** — retaining the LLM's own `token_estimate` only as a persisted shadow prediction for measuring disagreement.

## Alternatives considered

| Alternative | Pros | Cons | Why rejected |
|---|---|---|---|
| LLM → integer (status quo) | Simplest; one call | Unexplainable, unfalsifiable, un-tunable | The core defect being fixed |
| **LLM → drivers, harness → arithmetic** | Explainable on the card; falsifiable; calibration has a real target | Changes `EstimateResult` contract + all estimator tests/fixtures | **Chosen** |
| Reference-class / kNN over similar completed tasks | How humans estimate; emits a distribution | Cold-start; needs history | Kept as a later layer *on top of* drivers, not a replacement |
| Metered probe (launch N turns, extrapolate) | Most accurate | Costs real tokens | Now expressible cheaply as a Scout Task (ADR-0005) |
| Abandon prediction; meter and interrupt | Defensible for a governance harness | Deletes the board's estimate premise | Removes what makes the board legible |

## Consequences

- `EstimateResult` and its strict validator change shape; every estimator test and golden decomposition fixture moves with it. Blast radius is contained to `estimation.py` and its tests but is not free.
- The estimate becomes explainable in operator terms ("14 files, 7 turns, ~2.4k out/turn → 47k") and the LLM-vs-computed disagreement is persisted as a quality signal to prove the driver model beats a direct guess.
- **Coefficient provenance is per-driver, not per-estimate.** Each factor carries `seed` or `fitted(n)`. Turn-count and output-per-turn factors are fitted from the repository's recorded demo runs at ship time. The context/cache-growth factor **cannot** be fitted from the demo, because `demo_worker.py` deliberately holds cache counters at zero so its actual equals a plain input+output sum; it ships as a hand-authored `seed` and is replaced by the first real Worker Run with trustworthy cache-bearing per-turn evidence. The harness must not fabricate cache-bearing demo evidence to make a fitted factor look measured — an honestly labeled seed is preferred.
- Only Done tasks with trustworthy actuals (`native_usage`, not `observed_only`) feed fitting; Scout actuals do not calibrate implementation factors.
- Driver arithmetic is the **primary** path, not a fallback: an Estimator LLM failure yields no drivers and therefore no automatic estimate (manual estimate only), preserving the existing "never silently substitute a heuristic" rule.
- Coefficient residual variance is the intended source of future p50/p90 estimate bands and of reserved-budget headroom accounting — which is itself the prerequisite for concurrent Worker Runs on the Execution Floor (ADR-0002). Reference-class estimation is the intended later refinement.
