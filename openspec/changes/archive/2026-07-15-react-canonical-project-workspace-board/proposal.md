## Why

Slice 11a moved `/dashboard` and `/projects` onto build-aware React and left the other half of the inversion open: `/projects/{project_id}` and `/projects/{project_id}/board` still render Jinja, and their React equivalents live only under `/app/*`. The primary operator path — open a project, work its board — is the last surface where the canonical URL and the React view disagree.

This is the final blocker for the Jinja retirement change. Retirement makes `/app` a permanent redirect, which strands `/app/projects/{id}` and `/app/projects/{id}/board` as the only React-owned workspace and board URLs. It also closes the two link debts 11a knowingly took: project entry cards still point at `/app/projects/{id}`, and Board and Workspace still offer server-rendered escape links that 11a removed from the dashboard.

## What Changes

- `/projects/{project_id}` selects the React workspace when the complete build is available and renders the existing Jinja workspace when it is missing or partial. The backend's unknown-project `404` stays authoritative and is decided before the shell is served.
- `/projects/{project_id}/board` becomes build-aware the same way.
- An archived project opening `/projects/{project_id}/board` with the build available receives the React shell and React's existing archived-board state, which routes to Restore. The Jinja fallback keeps its current redirect to `/projects/{project_id}?error=…` for the missing/partial build. This retires a redirect at the canonical URL only when React is there to render the equivalent guard.
- React client routing claims `/projects/{project_id}` and `/projects/{project_id}/board`. `/app/projects/{id}` and `/app/projects/{id}/board` remain transitional aliases; this change does not make them redirects.
- Everything the shell navigates to moves onto the canonical project URLs, not just the card links 11a flagged:
  - Project entry cards on the React Projects list and dashboard target `/projects/{id}`.
  - FastAPI's projected workspace `board_href` and board-targeting attention hrefs become `/projects/{project_id}/board`, and the Restore success `next_href` becomes `/projects/{project_id}`.
  - Sidebar highlighting recognizes the canonical project and board routes, keeping the `/app` aliases highlighted while they exist.
- The "Open server-rendered board", "Open the server-rendered workspace", and "Open server-rendered history" escape links are removed, and those error branches adopt the established `safeError` treatment instead of raw `error.message`.

Not breaking: every canonical URL keeps its current behavior when the React build is missing or partial, `/app` deep links keep working, `/board` keeps its redirect shim, and no mutation changes shape.

## Capabilities

### New Capabilities

None. The migrated surfaces belong to the existing React Portal shell capability.

### Modified Capabilities

- `react-portal-shell`: route ownership adds the canonical `/projects/{project_id}` and `/projects/{project_id}/board`; the requirement that those two routes "SHALL continue to render Jinja until a following change migrates them" is replaced by build-aware React selection; the workspace JSON projection's fixed `board_href`, attention, and Restore `next_href` route ownership moves from `/app/projects/{id}` to the canonical URLs; dashboard and Projects entry cards target the canonical workspace; sidebar active-state recognizes the canonical project routes; archived-board behavior at the canonical URL is specified; and the server-rendered escape links are removed from the migrated error branches.

## Impact

- `src/foreman_ai_hq/routes/portal.py` — `project_workspace` and `project_board` become build-aware after their existing project lookup and archive checks.
- `src/foreman_ai_hq/routes/react_shell.py` — the workspace projection's `board_href`/attention hrefs and the Restore outcome's `next_href` target the canonical routes.
- `frontend/src/App.jsx` — `parseRoute` claims both canonical project routes alongside the retained `/app` aliases.
- `frontend/src/nav.jsx` — sidebar active-state recognizes the canonical project and board routes.
- `frontend/src/views/Projects.jsx`, `frontend/src/views/Dashboard.jsx` — entry links move to `/projects/{id}`.
- `frontend/src/views/Board.jsx`, `frontend/src/views/Workspace.jsx`, `frontend/src/views/TaskHistory.jsx` — escape links removed, error branches sanitized.
- `tests/portal/test_react_shell.py`, `frontend/tests/shell.test.mjs`.
- No schema change, no new JSON endpoints — `/api/projects/{id}/workspace` and `/api/projects/{id}/board` already exist and are consumed as-is. No new mutation routes; the launch, queue, review, and archive actions already negotiate JSON outcomes for React callers.

### Out of scope

- Making `/app` a redirect and deleting the duplicated Jinja templates — the final retirement change owns both, together.
- `/board`, which stays a redirect shim onto the first connected project's board.
- Login and the Portal Recovery Surface (slice 10), now unblocked by 11a's landing move.
- Unifying error-handling tiers across the views this change does not touch (Budget, Control Plane, Worker Settings, Alarms, Project Settings).
