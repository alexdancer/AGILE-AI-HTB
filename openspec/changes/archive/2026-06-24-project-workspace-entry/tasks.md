## 1. Project Routes

- [x] 1.1 Add authenticated `/projects` route that lists connected projects using existing `db.list_connected_projects` ordering and renders an open/connect repo form.
- [x] 1.2 Add authenticated `/projects/{project_id}` route that loads one connected project, refreshes Local Runner capability when available, and returns 404 for unknown ids.
- [x] 1.3 Change successful login redirect to the most recent connected project, falling back to `/projects` when none exist.

## 2. Templates

- [x] 2.1 Add a project list template that shows connected projects and reuses the existing connect local repo form action.
- [x] 2.2 Add a project overview template that shows repo identity, detected profile fields, capability state/reasons, and links to `/board`, `/sessions`, `/settings/workers`, and `/settings/project`.
- [x] 2.3 Update navigation minimally so project pages expose project context and keep global dashboard reachable.

## 3. Tests

- [x] 3.1 Add portal tests for `/projects` with and without connected projects.
- [x] 3.2 Add portal tests for `/projects/{project_id}` rendering project profile/capability data and unknown project 404 behavior.
- [x] 3.3 Add login redirect tests for most-recent project and no-project fallback.
- [x] 3.4 Run targeted portal tests and `pytest`.
