## Why

Markdown intake currently creates board Tasks by deterministic bullet/checklist splitting. That makes constraints and verification notes such as “Do not add network dependencies.” appear as bad standalone Tasks, which undermines the AGILE Board’s promise of agent-assisted vertical-slice orchestration.

## What Changes

- Replace deterministic Markdown splitting as a product behavior with a Task Breakdown Agent review flow.
- Persist durable Proposed Task Breakdown records before any imported Markdown or oversized text becomes board Tasks.
- Route Markdown uploads and Markdown paste to a separate breakdown review page, even when the agent returns a single-task decision.
- Show vertical-slice candidates, constraints, verification criteria, non-goals/rejected items, reasons, confidence, and lightweight recommended sequence.
- Let the operator practically edit and accept/reject candidates before estimation.
- Immediately run Task Estimation for accepted candidates and create Estimated AGILE Board cards; do not introduce a new accepted-but-unestimated backlog state.
- Add a separate configurable Task Breakdown Model in the control-plane/orchestrator model layer, with spend tracked as `task_breakdown` Orchestration Tokens.
- Replace tests that assert “N Markdown bullets create N Tasks” with tests/evals that assert “Markdown intake creates a durable review; no Tasks exist until acceptance.”
- Add golden decomposition fixtures that catch constraint/verification bullets being misclassified as implementation Tasks.
- **BREAKING**: Product intake no longer supports deterministic Markdown splitting as a direct task creation mode or fallback.

## Capabilities

### New Capabilities
- `task-breakdown-review`: Durable human review workflow for Task Breakdown Agent output before board Tasks are created.

### Modified Capabilities
- `markdown-task-intake`: Markdown upload/paste must create or route to a breakdown review before estimation, not directly create Tasks from deterministic bullet parsing.
- `estimator-task-decomposition-evals`: Evals must validate semantic vertical-slice decomposition, rejected-as-task reasons, and no task creation before review acceptance.
- `control-plane-model-connection`: Control-plane model configuration must distinguish the configurable Task Breakdown Model from the Estimator LLM and Worker Adapter models.

## Impact

- Affected code: task intake route, task creation/estimation orchestration, database schema/migrations for breakdown review records, templates/routes for the review page, settings/config for Task Breakdown Model, token ledger usage kind/category handling as needed.
- Affected tests: markdown task API tests, portal form tests, estimator/decomposition eval tests, model configuration tests.
- Affected docs: `CONTEXT.md`, OpenSpec specs, demo/runbook references that describe Markdown import behavior.
- No new network dependencies are expected; deterministic Markdown parsing may remain only as prompt structure hints for the Task Breakdown Agent.
