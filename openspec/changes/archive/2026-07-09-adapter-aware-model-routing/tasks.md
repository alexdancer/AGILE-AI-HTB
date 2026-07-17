## 1. Routing Contract and Tests

- [x] 1.1 Add focused tests for deterministic adapter-aware routing: direct guardrail match, selected-adapter substitute, default-adapter selection, no adapter, no allowed models, simple-task lightweight preference, large-task heavyweight preference, and budget clamp.
- [x] 1.2 Add API/task estimation tests proving `/estimate` never stores a `recommended_model` outside the selected/default Worker Adapter's allowed model set.
- [x] 1.3 Add regression tests for estimation success with no allowed Worker models: token/complexity evidence is preserved, no fake model is recommended, metadata points to Worker Setup, and launch remains blocked before Worker process start.

## 2. Deterministic Model Router

- [x] 2.1 Create a small domain module for Worker model routing that accepts guardrails, estimator result, budget context, selected/default adapter, and `allowed_worker_model_ids()` output.
- [x] 2.2 Move route-local model constraint/ranking logic out of `src/agile_ai_htb/routes/tasks.py` into the routing module while preserving lightweight/heavyweight ranking behavior.
- [x] 2.3 Implement deterministic guardrail tier selection and one-step budget-aware clamp using `guardrails.model_routing.budget_aware_clamp`.
- [x] 2.4 Return bounded routing metadata including selected adapter, guardrail policy candidate, selected model or no-model state, allowed model snapshot, budget clamp fields, and reason.

## 3. Estimator Contract

- [x] 3.1 Update `EstimateResult`, estimator prompt, parser, and validation so the LLM no longer owns or must return `recommended_model`.
- [x] 3.2 Ensure extra obsolete `recommended_model` output from the estimator cannot become the stored task recommendation.
- [x] 3.3 Preserve existing project context and calibration summary behavior for project-board and global estimation flows.

## 4. Route, Board, and Launch Integration

- [x] 4.1 Update `_estimate_and_create_task()` to call deterministic routing after estimator validation and before task creation.
- [x] 4.2 Persist the routed allowed Worker model as task `recommended_model` only when one is available; otherwise persist no static Worker model and record setup-incomplete metadata.
- [x] 4.3 Update Markdown intake accepted-candidate estimation to use the same routing path as direct `/estimate`.
- [x] 4.4 Update board rendering/API responses so estimator sizing evidence and Worker model routing provenance remain distinct and no unavailable model appears as the primary recommendation.
- [x] 4.5 Keep launch guardrails as the final compatibility check and verify they still reject missing/disallowed models before starting any Worker process.

## 5. Fixtures, Docs, and Verification

- [x] 5.1 Update fake estimator fixtures, calibration examples, and tests to remove LLM-owned `recommended_model` from estimator output while keeping Worker model provenance where appropriate.
- [x] 5.2 Update domain docs or OpenSpec main specs only as required by implementation behavior; avoid broad docs rewrites.
- [x] 5.3 Run targeted tests for estimator, task estimation, native Worker model discovery/routing, board launch selection, launch guardrails, and Markdown intake.
- [x] 5.4 Run `uv run pytest` and fix any regressions before marking tasks complete.
