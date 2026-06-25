## Why

AGILE Board runs still require too much operator babysitting: operators must manually refresh Running tasks, manually start Agent Review after successful Worker Runs, and manually launch each Estimated task one card at a time. The harness can automate those repetitive board operations while preserving the governance boundary that humans make final Review dispositions.

## What Changes

- Add project-scoped board run automation controls to the selected project board.
- Add live board refresh/polling so Running tasks move to Review or back to Estimated with retryable failure evidence without manual refresh clicks.
- Add an explicit `Run next task` action that launches the next eligible Estimated task for the selected project.
- Add an explicit `Run queue` action that launches eligible Estimated tasks one at a time for the selected project until a stop condition is reached.
- Add optional Auto Agent Review after successful Worker Runs, while keeping Agent Review advisory only.
- Record automation source, policy, start/stop reasons, and per-task actions as evidence visible on board/session surfaces.
- Preserve human-only Review disposition: automation SHALL NOT automatically Mark Done, Block, create repair tasks, or run cross-project autopilot.

## Capabilities

### New Capabilities
- `project-board-run-automation`: Project-scoped board automation for live run refresh, run-next, one-at-a-time run queues, optional Auto Agent Review, conservative stop conditions, and automation evidence.

### Modified Capabilities
- `board-launch-selection`: The board launch surface gains automation controls and live refresh behavior while preserving existing launch guardrails and inline failure evidence.
- `worker-run-lifecycle`: Worker Run completion and retryable failure states become automation inputs for queue continuation, stop reasons, and optional Auto Agent Review triggers.
- `task-review-disposition`: Review remains an operator decision point; Auto Agent Review may add advisory evidence but SHALL NOT automatically move tasks to Done or Blocked.
- `project-scoped-board`: Run automation is scoped to `/projects/{project_id}/board` and SHALL NOT launch tasks for a different connected project or fall back to the most-recent project.

## Impact

- Portal board route/template for project-scoped run automation controls, status counts, and live refresh/polling.
- Task launch/review routes or new automation routes for run-next, queue start/stop/status, and optional auto-review policy.
- Worker Run lifecycle integration for queue progression after Running tasks complete or fail.
- Database/task metadata for automation policy, queue state, automation source, and stop reasons.
- Tests for live refresh, run-next, project-scoped queue behavior, stop conditions, Auto Agent Review, and human-only Review disposition.
