## Why

Slices 1–9 each moved a surface onto its existing canonical URL, but Dashboard, Projects, project workspace, and Board predate that rule and are React-owned only under `/app/*`. Their canonical URLs still render Jinja, and `/projects` has no React view at all.

This blocks the final Jinja retirement. Retirement makes `/app` a permanent redirect to `/dashboard`, but `/dashboard` renders Jinja: deleting the templates breaks the redirect target, and keeping them strands the React dashboard behind a working-looking redirect. Either outcome is a regression that presents as success.

This change closes the first half of that gap (`/dashboard` and `/projects`), leaving project workspace and Board to a following slice. It goes first because it carries the only net-new work left in the inversion — `/projects` has no React view — and because Login's redirect target (`_default_portal_landing`) must be written once, to its final URL, rather than hardcoding `/app` and immediately rewriting it.

## What Changes

- `/dashboard` selects the React dashboard when the complete build is available and renders the existing Jinja dashboard when it is missing or partial, matching the build-aware pattern slices 1–9 established.
- `/projects` becomes build-aware the same way, backed by a new React Projects view. This is the net-new work: no React Projects view exists today.
- The React Projects view preserves what the Jinja page provides: the Open-local-repo form, the Local-Runner-disabled notice, per-project capability pills, project entry cards, Archive, and the archived list with Restore.
- `/api/projects` gains `archived_projects` and `local_runner_enabled`. Both derive from the helpers the Jinja page already uses; the addition is additive and does not change the existing `projects` array that Board, Workspace, and Task History consume.
- The normal authenticated landing (`_default_portal_landing`) targets `/dashboard` instead of `/app` when the complete build is available. The missing/partial-build landing is unchanged.
- React client routing claims `/dashboard` and `/projects`. `/app` continues to serve the shell as the transitional alias it was always specified to be; this change does not make it a redirect.
- The React dashboard's "Open the server-rendered dashboard" escape link is removed — it points at a surface this change makes a fallback rather than a destination.

Not breaking: every canonical URL keeps its current behavior when the React build is missing or partial, and `/app` deep links keep working.

## Capabilities

### New Capabilities

None. The migrated surfaces belong to the existing React Portal shell capability.

### Modified Capabilities

- `react-portal-shell`: the dashboard home moves from `/app` to the canonical `/dashboard` with `/app` retained as an alias; route ownership adds `/dashboard` and `/projects`; the default authenticated landing targets `/dashboard`; client-side navigation covers the Projects list; and two new requirements cover the Projects JSON projection and the Projects view's canonical build-aware behavior.

## Impact

- `src/foreman_ai_hq/routes/portal.py` — `/dashboard` and `/projects` become build-aware; `_default_portal_landing` targets `/dashboard`.
- `src/foreman_ai_hq/routes/react_shell.py` — `/api/projects` gains `archived_projects` and `local_runner_enabled`.
- `frontend/src/views/Projects.jsx` (new), `frontend/src/App.jsx` (routing), `frontend/src/views/Dashboard.jsx` (escape link removed).
- `tests/portal/test_react_shell.py`, `frontend/tests/shell.test.mjs`.
- No schema change, no new mutation routes, no changes to launch, estimation, budget, or archive semantics. `POST /projects/{id}/archive`, `POST /projects/{id}/restore`, and `POST /settings/project/connect` already negotiate JSON outcomes and are consumed as-is.

### Out of scope

- Canonical `/projects/{project_id}` and `/projects/{project_id}/board` — the following slice.
- `/board`, which is a redirect shim onto the first connected project's board and needs no React view.
- Login and the Portal Recovery Surface.
- Making `/app` a redirect and deleting the duplicated Jinja templates — the final retirement change.
- The dashboard estimation-accuracy drift and the error-handling tier inconsistency recorded in the plan's Known gap section.
