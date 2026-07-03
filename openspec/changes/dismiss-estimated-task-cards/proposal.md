## Why

Estimated task cards can clutter the active project board after an operator decides not to launch them, especially during task breakdown/demo cleanup. Operators need a per-card way to remove an Estimated card from the active board without deleting estimation evidence or inventing a new lifecycle state.

## What Changes

- Add a per-card **Dismiss** action for unarchived `Estimated` cards on `/projects/{project_id}/board`.
- Reuse existing task archive visibility metadata so dismissed Estimated tasks are hidden from the active board and remain available in project task history.
- Preserve the task lifecycle status as `Estimated` and preserve estimate/model/orchestration metadata.
- Keep scope intentionally narrow: no bulk dismiss, no hard delete, no `Dismissed`/`Archived` status, no board workflow rewrite.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project-scoped-board`: allow project-board operators to dismiss one `Estimated` card from active board visibility while preserving lifecycle status and evidence.
- `project-task-history`: require archived/dismissed `Estimated` tasks to remain visible in project task history with preserved estimate evidence and an unarchive path.

## Impact

- Board UI: add one per-card action for `Estimated` cards, labeled `Dismiss`.
- Task persistence: extend existing archive metadata behavior to `Estimated` tasks only for per-card dismissal.
- Task history UI/spec: ensure archived `Estimated` tasks remain auditable and restorable.
- Tests: add/update focused portal/database coverage for dismissing and unarchiving an Estimated task.
