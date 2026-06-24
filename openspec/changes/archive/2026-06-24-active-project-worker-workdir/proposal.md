## Why

Project workspace is now the portal entry point, so asking operators to also configure a separate Worker Adapter project directory is duplicate state. Worker launches should use the active project root as their repository boundary while Worker Adapter settings stay focused on CLI identity, auth, models, and tracking mode.

## What Changes

- Use the active project workspace root as the default Worker launch workdir.
- Stop requiring a per-adapter project workdir for normal board launches.
- Keep Worker Adapter configuration for adapter identity, default selection, model discovery, verification, auth/env, and tracking mode.
- Require normal board launches to have an active/selected connected project before invoking a Worker Adapter.
- Preserve explicit project-directory binding for OpenCode launches, including `opencode run --dir {active_project.root_path}` rather than relying on subprocess `cwd`.
- Keep diagnostic/verification flows available without pretending they select the project workspace.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `worker-adapter-verification`: Worker Adapter setup no longer owns normal task project workdir; launch readiness depends on adapter tracking verification plus active project availability.
- `board-launch-selection`: Board launch behavior requires an active project workspace and passes that root into the selected Worker Adapter launch.

## Impact

- Affected launch path: board task launch route and Worker launch planning.
- Affected adapter setup: Worker settings UI/copy and configure route behavior for `workdir`.
- Affected OpenCode adapter behavior: launch command must explicitly bind `--dir` to active project root.
- Existing data: reuse `connected_projects.root_path`; avoid schema migrations unless implementation proves an active-project pointer is needed.
- Tests: launch workdir selection, missing-active-project guardrail, Worker settings copy/config behavior, OpenCode command plan directory binding.
- Dependencies: no new dependencies.
