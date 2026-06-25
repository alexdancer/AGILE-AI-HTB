## 1. Queue state and automation policy

- [x] 1.1 Add a small persisted representation for project run automation state, including project id, status, active task/run ids, auto-review flag, source (`run_next` or `run_queue`), policy summary, and latest stop reason.
- [x] 1.2 Add helper functions to list eligible Estimated tasks for a selected project in deterministic board order.
- [x] 1.3 Add helper functions to record automation events and stop reasons on queue state and Worker Run/task metadata without changing existing task statuses.
- [x] 1.4 Add unit tests for eligible task selection, project scoping, no cross-project fallback, and queue stop reason persistence.

## 2. Live board refresh

- [x] 2.1 Add a lightweight project board status endpoint or polling response that marks stale Worker Runs interrupted, refreshes active task state, and returns enough data for the board to update or reload.
- [x] 2.2 Add server-rendered board UI polling/timed refresh for pages with Running tasks or active queue state, while keeping the manual Refresh status button available.
- [x] 2.3 Add portal tests proving Running tasks update to Review after success and to Estimated with inline launch evidence after retryable failure.

## 3. Run next and queue launch flow

- [x] 3.1 Add project-scoped `Run next task` route that launches exactly one eligible Estimated task through the existing `launch_task()` path with automation metadata.
- [x] 3.2 Add project-scoped `Run queue` start/stop/status routes that require an explicit project id and never start from ambiguous global board context.
- [x] 3.3 Implement one-at-a-time queue progression so the queue launches the next eligible task only after the active Worker Run reaches a terminal state.
- [x] 3.4 Allow queue continuation after a successful task enters Review while preserving human-only Review disposition.
- [x] 3.5 Add tests proving Run next launches one task, Run queue launches only one active Worker Run at a time, and Review tasks do not block the next eligible launch.

## 4. Guardrails and stop conditions

- [x] 4.1 Stop queue execution before launching when launch guardrails fail, no allowed model exists, the adapter is observed-only, the project root is missing/mismatched, or the task is not bound to the selected project.
- [x] 4.2 Stop queue execution before budget override or native usage budget acknowledgement would be required; do not auto-approve either condition.
- [x] 4.3 Stop queue execution on retryable Worker failures while preserving the task in Estimated with inline launch evidence.
- [x] 4.4 Stop queue execution on hard safety/manual blockers while preserving the existing Blocked lifecycle semantics.
- [x] 4.5 Add tests for budget-required, native-ack-required, observed-only adapter, project mismatch, retryable failure, hard blocker, no eligible tasks, and operator stop conditions.

## 5. Optional Auto Agent Review

- [x] 5.1 Add an automation policy flag for Auto Agent Review after successful Worker Runs.
- [x] 5.2 Trigger existing Agent Review logic after a queued Worker Run enters Review when Auto Agent Review is enabled.
- [x] 5.3 Record Auto Agent Review success or failure as advisory review evidence without moving the task to Done or Blocked.
- [x] 5.4 Add tests proving Auto Agent Review stores evidence, review failure leaves the task in Review, and approval/finding recommendations do not change Review Disposition.

## 6. Board UI and evidence

- [x] 6.1 Add a compact Run automation panel to `/projects/{project_id}/board` with eligible/running/review counts, `Run next task`, `Run queue`, stop action, Auto Agent Review option, and explicit policy copy.
- [x] 6.2 Ensure the global `/board` does not expose ambiguous queue start controls and points operators to project boards when automation needs a project context.
- [x] 6.3 Render latest queue status, stop reason, and automation events on board/session surfaces using existing timeline/details patterns.
- [x] 6.4 Add portal tests for automation panel rendering, policy copy, no global ambiguous queue, queue stop reason visibility, and manual launch form preservation.

## 7. Verification and documentation

- [x] 7.1 Update `CONTEXT.md` with `Board Run Queue`, `Auto Review`, and `Run Automation Policy` terms after implementation behavior is settled.
- [x] 7.2 Update relevant runbook/docs copy so operators understand Level 1-3 automation and the explicit no-auto-Done boundary.
- [x] 7.3 Run focused portal/worker lifecycle tests for the new automation behavior.
- [x] 7.4 Run the full `uv run pytest` suite and fix regressions.
