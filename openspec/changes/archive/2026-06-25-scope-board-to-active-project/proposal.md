## Why

The portal now makes operators feel like they have opened a specific project workspace, but the task board is still global. Selecting a project does not scope the board, task creation, or launch root, so a Worker launch can act on the wrong repository and demo work can land outside the repo the operator selected.

## What Changes

- Add a project-scoped task board at `/projects/{project_id}/board` and route project workspace board links to it.
- Show only tasks bound to the selected project on the project board.
- Bind new board-created tasks, estimate-form tasks, markdown task breakdowns, and accepted breakdown task cards to the selected project.
- Make Worker launch validate project binding and use the selected task/project root, not the most-recent connected project fallback.
- Keep `/board` safe by redirecting to the most-recent project board when a connected project exists, otherwise to `/projects`.
- Preserve the global dashboard/settings surfaces; this change is about board/task/launch project scoping, not Worker Adapter identity or model/tracking semantics.

## Capabilities

### New Capabilities
- `project-scoped-board`: Project workspace board routing, task visibility, task intake binding, and launch validation for a selected connected project.

### Modified Capabilities
- `project-workspace`: Project overview workflow links now route to the selected project's board instead of the global board.
- `board-launch-selection`: Board launch semantics now require the task's project binding to match the selected project board context.
- `worker-workdir-enforcement`: Worker launch root resolution now comes from the task/project binding rather than an implicit most-recent connected project fallback.

## Impact

- Affected routes/templates: project workspace, board rendering, task estimation/intake, task breakdown acceptance, task launch/review redirects.
- Affected persistence: task metadata gains required project binding fields for project-board tasks (`connected_project_id`, `project_root_path`, and project profile/root evidence); no dedicated schema migration is required for the first slice unless implementation proves metadata-only binding insufficient.
- Affected tests: portal project workspace tests, board filtering tests, task creation/estimate tests, task breakdown acceptance tests, and launch/workdir regression tests.
- No new Worker Adapter, model provider, tracking mode, or budget-accounting semantics are introduced.
