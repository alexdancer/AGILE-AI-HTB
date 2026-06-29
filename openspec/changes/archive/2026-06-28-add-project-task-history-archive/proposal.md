## Why

Done tasks should stop cluttering the active project board without losing the repo's task record. Operators need a separate repo-level history/archive page that keeps all task cards discoverable while the board stays focused on current work.

## What Changes

- Add a project task history/archive page for a connected repo that lists its task cards outside the active board.
- Add an Archive action for Done cards and an Archive all Done action for the selected project board.
- Keep archived tasks persisted as normal tasks; archive only changes board visibility.
- Hide archived tasks from the active board while keeping them visible in project task history.
- Add an Unarchive action from the history/archive page so archived Done tasks can return to the Done column.
- Preserve task lifecycle, Worker Run/session evidence, actual tokens, and estimation accuracy semantics.

## Capabilities

### New Capabilities
- `project-task-history`: Project-scoped task history/archive page that lists repo tasks, including archived Done cards, with filters and restore actions.

### Modified Capabilities
- `project-scoped-board`: Project boards can archive Done cards, archive all unarchived Done cards, and hide archived cards from the active board.

## Impact

- Affected portal routes/templates for `/projects/{project_id}/board` and a new project task history route.
- Affected task persistence helpers for archive/unarchive state stored on existing task metadata.
- Affected board/project tests for archive actions, board filtering, history listing, and evidence preservation.
- No new dependencies, no new task status, and no hard deletion of task rows.
