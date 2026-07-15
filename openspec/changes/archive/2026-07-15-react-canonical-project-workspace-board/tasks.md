## 1. Canonical route inversion

- [x] 1.1 Make `portal.py::project_workspace` build-aware: keep the existing project lookup and its `404`, then check `_react_index()` and serve the shell when complete, otherwise render the existing Jinja workspace (per design Decision 1 — check after the lookup, not before).
- [x] 1.2 Make `portal.py::project_board` build-aware the same way, keeping its existing `404`.
- [x] 1.3 In `project_board`, serve the shell for an archived project when the build is complete; preserve the existing redirect to `/projects/{project_id}?error=…` only for the missing/partial build (design Decision 2).
- [x] 1.4 Add an executable routing matrix over built × missing × partial for `/projects/{id}` and `/projects/{id}/board`, asserting React vs Jinja selection at each canonical URL for an active project.
- [x] 1.5 Add tests that an unknown project returns the existing `404` at both canonical routes in every build state, and never a `200` shell.
- [x] 1.6 Add tests for the archived board in both build states: React shell when built, redirect carrying the restore-first message when not.
- [x] 1.7 Add a test that `/board` keeps its existing redirect onto the first connected project's board, and onto `/projects` when none is connected.

## 2. Canonical href projections

- [x] 2.1 Change the workspace projection's active `board_href` and board-targeting attention hrefs to `/projects/{project_id}/board` (`react_shell.py`), leaving archived projects' `board_href: null` and `can_open_board: false` unchanged.
- [x] 2.2 Change the JSON Restore success outcome's `next_href` to `/projects/{project_id}`, leaving the `404` envelope's `retry_href: /projects` unchanged.
- [x] 2.3 Update the existing exact-href assertions to the canonical targets, and confirm each fails against the current `/app` projection before the change (design Risk: exact-href tests are the contract).
- [x] 2.4 Add a test that the HTML Restore caller still receives its unchanged `303` to `/projects/{project_id}`.

## 3. React routing and entry links

- [x] 3.1 Route `/projects/{id}` and `/projects/{id}/board` in `App.jsx::parseRoute`, keeping `/app/projects/{id}` and `/app/projects/{id}/board` as transitional aliases mapped to the same views.
- [x] 3.2 Point the React Projects list's active and archived entry cards at `/projects/{id}` (`Projects.jsx`), replacing the `/app/projects/{id}` targets 11a wrote deliberately.
- [x] 3.3 Point the React dashboard's project entry cards at the canonical workspace and board (`Dashboard.jsx`).
- [x] 3.4 Update `Board.jsx`'s archived-state route to Restore so it targets `/projects/{id}`.
- [x] 3.5 Make sidebar active-state recognize the canonical project and board routes while keeping the `/app` aliases highlighted (`nav.jsx`, design Decision 4).
- [x] 3.6 Add frontend tests for route parsing of both canonical URLs and both retained aliases, and for exact-suffix ownership so `/projects/{id}/task-history` is not swallowed by the workspace route.
- [x] 3.7 Add frontend tests that entry cards and sidebar highlighting target the canonical URLs, covering both a canonical path and an `/app` alias path.

## 4. Escape links and error branches

- [x] 4.1 Remove the "Open server-rendered board" link from `Board.jsx:138` and apply the established per-view `safeError` treatment to its raw `error.message`.
- [x] 4.2 Remove the "Open the server-rendered workspace" link from `Workspace.jsx:92` and sanitize that error branch the same way.
- [x] 4.3 Remove the "Open server-rendered history" link from `TaskHistory.jsx:83` and sanitize that error branch the same way (design Decision 5).
- [x] 4.4 Add frontend tests for all three sanitized error branches asserting no server-rendered link and no raw backend detail; mutation-check at least one by confirming it fails against the current escape-link branch.

## 5. Verification

- [x] 5.1 `openspec validate react-canonical-project-workspace-board --strict`.
- [x] 5.2 `uv run pytest -q`.
- [x] 5.3 `npm --prefix frontend run check`.
- [x] 5.4 Browser smoke: build the frontend, `uv run foremanctl serve --local-runner`, then open `/projects/{id}` and `/projects/{id}/board` from a Projects card, run a task through the board, archive the project, and confirm the archived board shows React's restore-first state.
- [x] 5.5 Fallback smoke: move `src/foreman_ai_hq/static/react/index.html` aside and confirm `/projects/{id}`, `/projects/{id}/board`, and the archived-board redirect all serve Jinja at the same URLs.
- [x] 5.6 Confirm no `/app/projects` target remains in `frontend/src/` or the workspace projection except the retained alias routes.
- [x] 5.7 `git diff --check`, then sync and archive the change.
