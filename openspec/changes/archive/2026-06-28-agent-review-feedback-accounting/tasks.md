## 1. Agent Review accounting

- [x] 1.1 Update Agent Review token recording so successful review usage is classified as control-plane reporting/orchestration spend with stable source/category metadata.
- [x] 1.2 Preserve Worker execution actuals by ensuring Agent Review tokens do not change `task.actual_tokens` or `worker_execution` totals.
- [x] 1.3 Add or update token breakdown tests proving Agent Review spend appears in total tracked budget visibility and not Worker execution actuals.

## 2. Review result metadata and board feedback

- [x] 2.1 Store Agent Review session id, model, reviewed timestamp, status, recommendation/summary, findings, and token totals in the task's `agent_review` metadata.
- [x] 2.2 Update the Review task card to show a concise visible Agent Review completed/failed line after the action returns, without requiring raw details expansion.
- [x] 2.3 Keep detailed findings and raw review evidence behind the existing Review details section.
- [x] 2.4 Add or update board/review tests for visible completion, visible failure, session id/model/token display, and unchanged Review lifecycle state.

## 3. Session evidence surfaces

- [x] 3.1 Update sessions index/report context so Agent Review sessions are recognizable as review sessions with model, status, and token totals.
- [x] 3.2 Link or identify the Agent Review session from the task card when available.
- [x] 3.3 Add or update session/report tests proving Agent Review session evidence appears compactly and raw details remain secondary.

## 4. Verification

- [x] 4.1 Run `openspec validate agent-review-feedback-accounting --strict`.
- [x] 4.2 Run targeted tests for task review, board rendering, budget/token breakdown, and session evidence.
- [x] 4.3 Run `uv run pytest` before marking implementation tasks complete.
