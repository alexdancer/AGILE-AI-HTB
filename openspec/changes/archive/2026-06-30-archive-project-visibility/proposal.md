## Why

Operators can archive Done task cards, but old connected repos/projects still clutter the project list, sidebar, setup recents, and default board routing. We need a non-destructive way to hide stale projects while preserving task, session, and evidence history.

## What Changes

- Add project archive visibility for connected projects: Archive hides a project from active project surfaces; Restore makes it active again.
- Preserve connected-project rows, filesystem repos, project tasks, Worker Runs, sessions, token evidence, and history.
- Hide archived projects from the sidebar, `/projects` active list, setup project summary, and `/board` default redirect.
- Show archived projects behind an explicit archived section/filter with Restore actions.
- Block project archive while the project has Running work or active run automation.
- Re-opening the same local repo restores the archived project or clearly routes the operator to restore it.
- Do not add hard delete, filesystem deletion, a new project-history table, SPA UI, or Worker Adapter changes.

## Capabilities

### New Capabilities
- `project-archive-visibility`: Visibility-only archiving and restoring for connected projects/repositories.

### Modified Capabilities
- `project-scoped-board`: Default board routing and project board access must treat archived projects as hidden from active launch surfaces unless the operator opens the archived project directly.

## Impact

- Database: add explicit project archive state to `connected_projects`.
- Portal routes/templates: project list, sidebar context, project settings, project workspace, and `/board` redirect.
- Local project connect flow: same root path should not create duplicates; it should restore or expose restore for an archived project.
- Tests: DB migration/default list behavior, portal project visibility, archive/restore actions, `/board` routing, and running-work archive block.
