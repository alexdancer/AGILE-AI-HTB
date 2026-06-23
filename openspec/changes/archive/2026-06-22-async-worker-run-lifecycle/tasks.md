## 1. Persistence and Lifecycle Model

- [x] 1.1 Add SQLite persistence for Worker Run records linked to task ID and session ID, including adapter ID, model, tracking mode, command plan metadata, status, timestamps, return code, timeout/error details, and sanitized stdout/stderr evidence.
- [x] 1.2 Add DB helpers for creating Worker Runs, marking them running/completed/failed/interrupted, querying the active run for a task, and listing run evidence for board/session display.
- [x] 1.3 Add migration/default handling for existing `Ready` tasks so they are treated as `Estimated` and no new Ready tasks are created.

## 2. Async Launch Execution

- [x] 2.1 Refactor `launch_task()` or introduce a launch-start path that validates guardrails, creates the Worker session/run, marks the task `Running`, schedules execution, and returns without waiting for subprocess completion.
- [x] 2.2 Implement the in-process background Worker Run executor that runs existing Worker Adapter command plans and records completion/failure evidence through the new DB helpers.
- [x] 2.3 Prevent duplicate active Worker Runs for a task by rejecting or returning the existing active run when Launch is clicked while the task is already Running.
- [x] 2.4 Preserve existing tracking-mode checks for proxy-governed and native-usage launches in the background completion path.

## 3. Completion and Failure Transitions

- [x] 3.1 On successful Worker Run completion with required evidence, move the task from `Running` to `Review` and preserve stdout/stderr, session/token evidence, and git diff/porcelain evidence when a project root is connected.
- [x] 3.2 On retryable Worker Run timeout, nonzero exit, or missing usage evidence, mark the run/session failed and return the task to `Estimated` with inline retryable error metadata.
- [x] 3.3 Keep hard safety failures, workflow/dependency blockers, read-only mutation, and write-capable verification failures mapped to `Blocked` with preserved evidence.
- [x] 3.4 Detect stale active in-process runs after restart or lost executor ownership and surface them as interrupted retryable failures.

## 4. Board and API Contract

- [x] 4.1 Remove `Ready` from canonical task statuses, board columns, launch-form rendering, and copy that describes the board lifecycle.
- [x] 4.2 Update `/tasks/{task_id}/launch` responses so HTML and JSON callers get an immediate non-blocking response after Worker Run start.
- [x] 4.3 Update the board template so `Estimated` tasks are launchable, `Running` tasks show active Worker Run state, `Review` tasks show completion evidence, and retryable failures remain visible on `Estimated` cards.
- [x] 4.4 Add or update refresh/polling behavior so the board can reflect Running/Review/error state without blocking navigation.

## 5. Tests and Verification

- [x] 5.1 Add tests proving Launch returns before a long-running Worker Adapter command completes and the task is visible as Running.
- [x] 5.2 Add tests proving successful background completion moves the task to Review with stdout/stderr, session/token evidence, and project diff evidence where applicable.
- [x] 5.3 Add tests proving timeout/nonzero/missing-usage failures return the task to Estimated with retryable inline error metadata and do not move to Blocked.
- [x] 5.4 Add tests proving duplicate Launch requests do not start multiple active Worker Runs for the same task.
- [x] 5.5 Add tests proving Ready is no longer rendered or created and existing Ready tasks are treated as Estimated.
- [x] 5.6 Run targeted task launch/board/local execution tests and the full `uv run pytest` suite before marking implementation tasks complete.
