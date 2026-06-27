## 1. Token persistence

- [x] 1.1 Add a focused test proving a successful Worker Run records `tasks.actual_tokens` from session `worker_execution` token usage when the task enters Review.
- [x] 1.2 Update the Worker Run completion path to set `actual_tokens` from `db.session_token_breakdown(...)["by_category"]["worker_execution"]` after required usage evidence passes.
- [x] 1.3 Add or update a Review disposition test proving Mark Done preserves the recorded actual token total.

## 2. Board card Launch details

- [x] 2.1 Add a portal board test for a successful launched task where the `Launch` details section contains visible Worker launch/run evidence instead of rendering blank.
- [x] 2.2 Update board card launch-detail rendering to show useful existing evidence such as adapter, model, tracking mode, command plan/workdir, return code, launch errors, blocked reasons, or failure payloads.
- [x] 2.3 Ensure the board hides Launch details or shows an explicit unavailable message when no launch/run evidence exists, without showing an empty disclosure.

## 3. Verification

- [x] 3.1 Run targeted tests for Worker Run completion, Review disposition, and board rendering.
- [x] 3.2 Run `openspec validate improve-board-card-launch-and-actual-tokens --strict`.
- [x] 3.3 Run the relevant broader pytest slice for affected portal/task launch tests.
