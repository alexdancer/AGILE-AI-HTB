## Why

The dashboard currently shows Agent Review/control-plane reporting tokens in “Tokens Used” while the daily budget card remains `0 / cap` because budget usage is computed from `worker_execution` only. That makes the operator believe 4,942 real model tokens were tracked but did not consume budget, which contradicts the product expectation that governed orchestration spend is budgeted.

## What Changes

- Count all governed model-spend categories toward the daily budget usage and budget zone, including control-plane estimation, task breakdown, reporting/Agent Review, adapter verification, and Worker execution tokens.
- Preserve task `actual_tokens` as Worker execution only, so Agent Review/control-plane reporting tokens do not inflate Worker completion evidence or estimation accuracy.
- Update dashboard and token budget copy so “Daily budget” means total governed model spend, not Worker execution only.
- Show a category breakdown that makes Agent Review/reporting/control-plane orchestration spend visible instead of hiding it behind `control-plane 0 · worker 0`.
- Update Worker launch budget guardrails to use the same daily consumed total when checking remaining daily budget, while still comparing per-session execution estimates against the per-session Worker execution cap.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `token-budget-setup`: Daily budget usage and zones count governed orchestration/reporting/setup tokens as well as Worker execution tokens, while Worker task actuals remain Worker-only.

## Impact

- Affected code: token budget aggregation helpers, launch budget checks, dashboard route context, dashboard template copy/breakdown, token budget settings copy, and related portal/budget tests.
- Affected behavior: Agent Review/control-plane reporting tokens consume daily budget capacity and influence daily budget alarm/zone calculations.
- Not affected: Worker Adapter auth/model selection, Agent Review model-layer choice, task lifecycle states, task `actual_tokens`, session token logs, or estimation accuracy calculations.
- No new dependencies, schema migrations, Worker Adapter changes, or frontend rewrite.
