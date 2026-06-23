## Why

Launching a task from the board currently runs the Worker adapter inside the HTTP request. For long-running OpenCode/Codex/Claude/demo-worker sessions this makes the website wait on the coding agent and obscures the product lifecycle: launch should start work, not block the operator until work is finished.

This change makes Worker execution an asynchronous run lifecycle: clicking Launch moves a task from Estimated to Running immediately, the board remains navigable, and completion of the background Worker Run moves the task to Review with captured evidence.

## What Changes

- **BREAKING**: Remove the `Ready` board column from the canonical task lifecycle; `Estimated` is the launchable pre-run state once estimation/model/adapter guardrails pass.
- Launching a task creates a background Worker Run and returns immediately instead of waiting for the adapter subprocess to finish.
- Worker Run success moves the task from `Running` to `Review` and records stdout/stderr, session/token evidence, and git diff/porcelain evidence when a project root is connected.
- Worker Run timeout or nonzero exit moves the task back to `Estimated` with an inline retryable run error; it does not use `Blocked` unless the failure is a workflow/manual/safety blocker.
- The board remains usable while Worker Runs are active and can show Running/Review/error state from persisted run metadata.
- Use an in-process background runner for the first implementation slice, backed by SQLite records, without introducing Redis/Celery or hosted queue infrastructure.

## Capabilities

### New Capabilities
- `worker-run-lifecycle`: Tracks asynchronous Worker Run creation, execution, completion, evidence capture, and retryable failure state.

### Modified Capabilities
- `board-launch-selection`: Removes the redundant `Ready` column, makes `Estimated` the launchable board state, and requires Launch to return immediately so the board remains navigable.
- `governed-worker-launch`: Changes launch from synchronous adapter execution to asynchronous Worker Run start while preserving launch guardrails and operational-vs-blocking failure semantics.
- `local-execution-backend`: Defines the first background execution slice as an in-process local runner with persisted SQLite run metadata rather than a separate queue service.

## Impact

- Affected UI/templates: board columns, launch forms, Running/Review/error display, optional polling/refresh behavior.
- Affected API routes: `/tasks/{task_id}/launch`, task refresh/status endpoints, and any response contracts that currently assume launch completion.
- Affected launch code: `task_launch.py`, adapter command execution, subprocess timeout handling, output/evidence capture, and task status transitions.
- Affected persistence: task metadata and/or new Worker Run records in SQLite for run status, command plan, stdout/stderr, return code, timeout/error details, session/token evidence, and git diff evidence.
- Affected tests: launch endpoint should return quickly, task transitions should be asynchronous, success should end in Review, retryable failure should return to Estimated, and Blocked should remain reserved for workflow/manual/safety blockers.
