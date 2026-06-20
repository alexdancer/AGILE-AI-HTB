## Why

Local demo launch testing exposed that an operational Worker launch timeout can move an otherwise estimated task into the `Blocked` column, making it impossible to relaunch and confusing workflow dependency blocking with recoverable infrastructure failure. The same test notes also show missing markdown task intake, insufficient validation of repo-aware/bullet-point task estimation, and unclear behavioral coverage for budget alarms.

## What Changes

- Preserve launchable task lifecycle when Worker launch fails for recoverable operational reasons such as timeout, adapter command failure, or missing proxy usage evidence; surface the failure as inline launch error metadata/UI instead of treating the task as workflow-blocked.
- Keep the `Blocked` column for explicit workflow/dependency blocks, manual-estimate-required tasks, unsupported lifecycle transitions, or real multi-part task blockers similar to issue dependencies.
- Make the local demo Worker launch path realistic for real provider latency by avoiding the current 60-second hard stop as the default behavior for model-backed demo runs.
- Add markdown task intake for the estimator so an operator can paste or upload a `.md` task description from the board/API instead of only using a one-line text input.
- Add behavioral eval coverage proving repo-aware, longer, and bullet-point markdown tasks are estimated/decomposed correctly enough for the demo.
- Add alarm/observability eval coverage proving budget zone, daily cap, and session cap alarms fire at the right boundaries and remain visible in dashboard/session report flows.

## Capabilities

### New Capabilities

- `markdown-task-intake`: Board/API intake of markdown task descriptions, including `.md` file input and estimator normalization for multi-line/bullet-point tasks.
- `estimator-task-decomposition-evals`: Behavioral evals for repo-aware estimation and decomposition of longer or bullet-point task descriptions into appropriate estimated work items or breakdown metadata.
- `budget-alarm-behavior-evals`: Behavioral evals for budget alarm generation, deduplication, and UI/report visibility across budget zones and cap boundaries.

### Modified Capabilities

- `board-launch-selection`: Launch failures for Estimated/Ready tasks must be shown as inline recoverable launch errors while preserving relaunchability unless the operator explicitly marks a workflow block.
- `governed-worker-launch`: Worker launch timeout/adapter failure semantics must distinguish operational launch failure from workflow blocking, while preserving sanitized launch evidence.
- `local-execution-backend`: Local/demo Worker execution must support real model-call latency without defaulting to a 60-second failure for normal demo runs.
- `budgeted-launch-control`: Budget alarms and launch-budget evidence must be behaviorally verified without conflating control-plane/setup spend with Worker execution enforcement.

## Impact

- Affected code:
  - `src/agile_ai_htb/task_launch.py`
  - `src/agile_ai_htb/worker_adapters.py`
  - `src/agile_ai_htb/demo_worker.py`
  - `src/agile_ai_htb/routes/tasks.py`
  - `src/agile_ai_htb/routes/portal.py`
  - `src/agile_ai_htb/routes/proxy.py`
  - `src/agile_ai_htb/alarms.py`
  - `src/agile_ai_htb/templates/board.html`
- Affected specs:
  - existing launch, local execution, board, and budget-control specs listed above
  - new markdown intake and eval-focused specs
- Affected tests/evals:
  - launch lifecycle tests that currently expect operational failures to move tasks to `Blocked`
  - board form/API tests for markdown intake
  - estimator behavioral evals for real-repo and bullet-point task inputs
  - alarm behavior evals for budget zones, cap boundaries, deduplication, dashboard visibility, and session-report visibility
- No dependency changes are expected unless file upload parsing requires additional test/client support beyond FastAPI's existing form handling.
