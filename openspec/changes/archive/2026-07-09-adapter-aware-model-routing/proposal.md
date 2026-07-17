## Why

Task estimation currently lets the estimator appear to own Worker model choice before route-level correction rewrites or blocks it because the selected/default Worker Adapter cannot use that model. This makes the card model feel untrustworthy: the operator wants the routed Worker model to already be launch-compatible with the Worker Adapter's approved model set.

## What Changes

- Move Worker model choice from LLM-owned output plus route-level correction into deterministic, adapter-aware routing after estimation.
- Keep the estimator focused on task size, complexity, confidence, rationale, assumptions, and risk flags.
- Select the task `recommended_model` only from the selected/default Worker Adapter's operator-approved allowed Worker models.
- Treat an empty allowed model set as setup-incomplete: estimation may still produce token/complexity evidence, but routing must not store a static assumed Worker model or imply launch readiness.
- Preserve provenance metadata showing estimator complexity, guardrail policy candidate, selected adapter, selected allowed Worker model, and routing reason.
- Enforce budget-aware model clamp in code rather than only including it in the estimator prompt.
- Keep launch guardrails as the final safety check for model compatibility before starting any Worker process.

## Capabilities

### New Capabilities
- `adapter-aware-model-routing`: Deterministic Worker model routing that combines estimator complexity, guardrail policy, budget clamp, and Worker Adapter allowed models before storing the routed task model.

### Modified Capabilities
- `native-worker-model-discovery`: Strengthen Worker model routing constraints so the stored routed task model is selected from the adapter's allowed Worker model set, not merely corrected after incompatible LLM output.
- `estimator-project-context`: Change Task Estimation output contract so the estimator no longer owns Worker model choice; it supplies complexity and estimate evidence consumed by deterministic routing.
- `board-launch-selection`: Ensure board cards and launch controls treat the stored routed model as adapter-compatible provenance while preserving launch-time override and guardrail validation behavior.

## Impact

- Affected code: `src/agile_ai_htb/estimation.py`, `src/agile_ai_htb/routes/tasks.py`, guardrails model-routing config loading/usage, Worker adapter allow-list helpers, task/board tests, estimator eval tests, calibration fixtures, and launch guardrail tests.
- Affected behavior: `/estimate`, Markdown intake accepted-candidate estimation, board card model display, Worker Adapter model allow-list handling, and task metadata/provenance.
- No new external dependencies.
- No database schema change required for the first slice; routing provenance can remain task metadata unless implementation discovers existing metadata is insufficient.
