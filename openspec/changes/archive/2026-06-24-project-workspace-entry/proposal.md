## Why

The portal currently treats the repo as a setup detail under Connected project. Operators want the portal to feel like opening Hermes, Claude Code, OpenCode, or Codex inside a specific directory: project first, harness controls second.

## What Changes

- Add a first-class project workspace entry flow.
- Add `/projects` for connected projects plus the existing open/connect repo form.
- Add `/projects/{project_id}` as a repo-specific overview page using the existing connected project profile and capability checks.
- Redirect successful login to the most recently connected project when one exists; otherwise fall back to project selection.
- Link from the project overview to existing board, sessions, Worker adapter, and project settings pages instead of rebuilding those flows.
- Keep global dashboard, board, sessions, alarms, and settings available.
- Do not add project-scoped board/session/report implementations in this slice.

## Capabilities

### New Capabilities
- `project-workspace`: Project workspace entry, project list/open flow, project overview, and project-first login redirect.

### Modified Capabilities

None.

## Impact

- Affected routes/view models: `src/agile_ai_htb/routes/portal.py`
- Affected UI: new or reused Jinja templates under `src/agile_ai_htb/templates/`
- Existing data: reuse `connected_projects`, profile JSON, capability JSON, and current Local Runner project connection logic
- Existing destinations: `/board`, `/sessions`, `/settings/workers`, `/settings/project`
- Tests: portal project list, project overview, login redirect, and missing-project behavior
- Dependencies: no new dependencies
