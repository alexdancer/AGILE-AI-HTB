## 1. Projects JSON handoff

- [x] 1.1 Extend `react_shell.py::react_projects_state` with `archived_projects` and `local_runner_enabled`, deriving both from the same `_archived_project_view_models` and settings flag the Jinja `/projects` route uses; leave the existing `projects` array untouched.
- [x] 1.2 Bound archived rows to `id`, name, root path, sanitized capability state, and archive timestamp; type absent optional values as `null`.
- [x] 1.3 Add tests: auth rejection; the added fields' key allowlist; agreement with the Jinja projects page for the same database state; capability reasons bounded by the evidence-safety helper.
- [x] 1.4 Add a test asserting the existing `projects` array keeps its current fields, ordering, and task counts, so Board, Workspace, and Task History stay unaffected.

## 2. Canonical route inversion

- [x] 2.1 Make `portal.py::dashboard` build-aware: check `_react_index()` before computing dashboard state, serve the shell when complete, render the existing Jinja dashboard otherwise.
- [x] 2.2 Make `portal.py::projects` build-aware the same way.
- [x] 2.3 Register `/dashboard` and `/projects` on the React shell route so a full page load resolves them, without adding any `/app/projects` alias.
- [x] 2.4 Point `_default_portal_landing` at `/dashboard` instead of `/app` for the build-available branch; leave the first-project/`/projects` fallback branch unchanged.
- [x] 2.5 Add an executable routing matrix over auth-required × auth-disabled and built × missing × partial for `/`, `/login`, `/logout`, `/dashboard`, and `/projects`, asserting React vs Jinja selection at each canonical URL.
- [x] 2.6 Add a test that the fallback landing's `/projects` target renders Jinja for the same build state that caused the fallback.
- [x] 2.7 Add a test that `/board` keeps its existing redirect onto the first connected project's board, and onto `/projects` when none is connected.

## 3. React Projects view

- [x] 3.1 Add `frontend/src/views/Projects.jsx` rendering the open-local-repo form, Local-Runner-disabled notice, active project entry cards with capability pills, Archive, and the archived list with Restore and archive timestamps.
- [x] 3.2 Consume the existing negotiated JSON outcomes of `POST /settings/project/connect`, `POST /projects/{id}/archive`, and `POST /projects/{id}/restore` unchanged; refetch authoritative projects state after each success rather than trusting submitted values.
- [x] 3.3 Surface the backend's sanitized archive block reason; add a local `safeError` matching the existing per-view pattern so no raw backend detail reaches the operator.
- [x] 3.4 Link project entry cards to `/app/projects/{id}` for in-shell navigation (per design Decision 2; the following slice rewrites this to `/projects/{id}`).
- [x] 3.5 Route `/dashboard` and `/projects` in `App.jsx::parseRoute`, keeping `/app` mapped to the dashboard as the transitional alias.
- [x] 3.6 Add frontend tests for route parsing of both canonical URLs and the retained `/app` alias.

## 4. Dashboard corrections

- [x] 4.1 Hide the estimation-accuracy panel entirely when `completed_count` is null, matching `dashboard.html:143`; leave the non-null-under-three progress state as-is.
- [x] 4.2 Mutation-check that test: confirm it fails against the current unconditional panel before the fix, not merely passes after it.
- [x] 4.3 Remove the "Open the server-rendered dashboard" link from the `Dashboard.jsx` error branch and apply the established `safeError` treatment to the raw `{error.message}` in that branch.
- [x] 4.4 Add a dashboard entry point to the canonical `/projects` list.
- [x] 4.5 Add frontend tests for the accuracy panel's absent/progress/figures states and for the sanitized error branch without an escape link.

## 5. Verification

- [ ] 5.1 `openspec validate react-canonical-dashboard-projects --strict`.
- [ ] 5.2 `uv run pytest -q`.
- [ ] 5.3 `npm --prefix frontend run check`.
- [ ] 5.4 Browser smoke: build the frontend, `uv run foremanctl serve --local-runner`, then open `/dashboard` and `/projects`, connect a repo, archive and restore a project, and confirm the fresh-install dashboard shows no accuracy panel.
- [ ] 5.5 Fallback smoke: move `src/foreman_ai_hq/static/react/index.html` aside and confirm `/dashboard`, `/projects`, and the default landing all serve Jinja at the same URLs.
- [ ] 5.6 `git diff --check`, then sync and archive the change.
