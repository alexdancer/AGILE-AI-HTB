## Why

Completed task cards can hide the only number operators care about after a Worker finishes: actual Worker execution tokens. The board also exposes an expandable `Launch` section that can render empty, making operators unsure whether launch evidence is missing or the UI is broken.

## What Changes

- Record actual Worker execution token totals on the task when a successful Worker Run reaches Review.
- Preserve the recorded actual token total when an operator marks the task Done.
- Make board card token copy distinguish unavailable actual usage from a real zero-token value.
- Make the `Launch` details section either show useful launch/run evidence or not appear blank.
- Clarify `Launch` as Worker launch/run evidence: adapter, model, tracking mode, command plan/workdir evidence, return code, and failure/blocked evidence when available.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `board-card-readability`: Completed/reviewable task cards must surface actual Worker execution token totals and must not render an empty Launch details section.
- `worker-run-lifecycle`: Successful Worker Run completion must derive and persist task-level actual token totals from authoritative Worker execution usage evidence.
- `task-review-disposition`: Mark Done must preserve task-level actual token and Worker Run evidence collected before disposition.

## Impact

- Affected code: board card rendering, Worker Run completion, Review disposition, and existing board/task review tests.
- Data model: no schema migration expected; reuse `tasks.actual_tokens`, `token_turns`, `worker_runs`, and task metadata.
- Dependencies: none.
