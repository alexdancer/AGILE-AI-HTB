## Why

Project selection exists, but it still feels like a settings detail instead of opening the portal inside a repo. Operators need a cleaner Codex-style project switcher so they can see and switch local repositories from the main navigation without hunting through setup/settings pages.

## What Changes

- Show connected project repositories directly in the sidebar as first-class navigation.
- Highlight the active project when browsing a project workspace or project board.
- Link each sidebar project to its project workspace and keep the selected project's board one click away.
- Rename primary operator-facing copy from "Connected project" toward "Projects", "Open local repo", and "Switch project" where the screen is about repo selection.
- Keep existing project list, project overview, project-scoped board, dashboard, sessions, and settings routes.
- Do not add a new schema, SPA shell, drag/drop navigation, or repo search in this slice.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project-workspace`: add project switcher/sidebar navigation behavior for connected repositories.

## Impact

- Affected UI: portal base/sidebar template, project list/workspace templates, settings/project copy.
- Affected routes: project workspace pages may need to pass connected project navigation context into templates.
- Affected tests: portal navigation/sidebar rendering for no-project, multi-project, and active-project states.
- No database schema change and no Worker Adapter model/tracking semantic change.
