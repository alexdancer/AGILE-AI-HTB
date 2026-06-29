## Why

Agent Review currently completes without an obvious board response, and its control-plane review spend is not surfaced as a first-class budget/session signal. Operators need Agent Review to stay advisory while making completion, model, session, and token evidence visible enough to act on.

## What Changes

- Keep Agent Review as control-plane/orchestrator review work, not a Worker Adapter launch.
- Classify Agent Review token usage as orchestration/reporting spend that counts in total daily budget visibility without inflating Worker execution actuals.
- Show a concise Agent Review completion/failure line on the Review task card after the action finishes.
- Link or identify the Agent Review session from the task card and session surfaces, including review model and token totals.
- Preserve current Review disposition behavior: Agent Review does not automatically Mark Done or Block.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `task-review-disposition`: Clarify that completed Agent Review must leave visible advisory evidence, review session identity, model, and token totals on the Review task.
- `board-launch-selection`: Strengthen the board requirement so redirected Review cards show an obvious Agent Review response after the action completes.
- `token-budget-setup`: Require Agent Review orchestration tokens to be categorized in budget summaries and total tracked usage while remaining separate from Worker execution actuals.
- `portal-evidence-readability`: Require session/report surfaces to expose Agent Review session evidence compactly before raw detail.

## Impact

- Affected code: Review action route, Agent Review helper, token usage categorization/breakdown, board task card template, sessions index/report context, and related tests.
- Affected APIs/UI: `/tasks/{task_id}/review` Agent Review action, AGILE Board Review cards, `/sessions`, and `/sessions/{session_id}`.
- Dependencies: none.
