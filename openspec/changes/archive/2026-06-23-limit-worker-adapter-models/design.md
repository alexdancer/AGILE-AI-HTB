## Context

Worker Adapter model discovery currently feeds `worker_adapters.supported_models_json`, and existing estimate, board, and launch paths already use that field as the model constraint. The missing product distinction is between all models discovered from the Worker CLI and the subset the operator allows AGILE-AI-HTB to recommend or launch.

The control-plane/orchestrator model remains separate: it estimates task size and complexity. The Worker/coding harness models are selected from the active Worker Adapter's allowed models.

## Goals / Non-Goals

**Goals:**

- Let operators approve a subset of discovered Worker models after discovery.
- Use the approved subset for estimator Worker recommendations and board manual model selection.
- Block launches for models outside the approved subset.
- Preserve discovered-model evidence for visibility and future re-selection.
- Keep adapter identity and tracking mode semantics unchanged.

**Non-Goals:**

- No new provider abstraction or API-key flow.
- No control-plane estimator model setting changes.
- No new table unless implementation proves existing fields insufficient.
- No automatic budget/model policy language beyond the allow-list.

## Decisions

1. Reuse existing persistence.
   - Store discovered inventory in existing adapter config evidence (`config.model_discovery`).
   - Store the operator-approved allow-list in existing `supported_models_json`.
   - Rationale: current estimate, board, readiness, and launch checks already read `supported_models`; reusing it is the shortest root-cause path.
   - Alternative rejected: add `allowed_models_json`; this duplicates model lists and requires broader call-site changes.

2. Discovery does not silently grant new models.
   - Re-running discovery updates evidence, but governed use continues to depend on the operator-approved subset.
   - If no allow-list exists yet, discovery leaves the adapter not launchable until the operator saves an allowed subset; seeded preset model lists are not treated as operator approval.
   - Rationale: explicit operator approval is the point of the feature.

3. UI stays in Worker Setup.
   - Add a small allowed-model checkbox form below discovery for the active adapter.
   - Rationale: discovery and approval are one setup flow; no board rewrite.

4. Existing launch guardrails remain authoritative.
   - `evaluate_adapter_readiness(model=...)` already rejects unsupported models, so implementation should make `supported_models` mean allowed models everywhere.
   - Rationale: one shared guard is less code and fewer bypasses.

## Risks / Trade-offs

- Existing code/tests may call `supported_models` "discovered models" → update labels and tests to clarify it now means allowed models for governed use.
- Operators may deselect all models → adapter becomes not launchable until at least one model is allowed.
- Discovery evidence shape may vary by adapter → read model IDs from the existing normalized discovery result/evidence, not raw provider-specific output.
