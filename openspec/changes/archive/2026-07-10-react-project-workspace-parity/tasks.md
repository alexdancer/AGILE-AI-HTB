## 1. Backend workspace contract

- [x] 1.1 Inspect current `react_project_workspace_state`, `_project_view_model`, `project_workspace_summary`, archive/restore handlers, and existing React/Jinja workspace tests; record the exact fields and legacy HTML behavior that must remain unchanged.
- [x] 1.2 Replace the React workspace handoff with the design's exact `project`/`summary`/`controls`/`links` schema, nested key allowlists, scalar/list bounds, redaction-before-truncation, typed null/empty defaults, and malformed-value safety; preserve unknown-project 404 and portal-auth behavior.
- [x] 1.3 Ensure projected board-targeting attention actions use `/app/projects/{project_id}/board`, while task history, Sessions, Worker setup, and Project settings retain only their allowed Jinja URLs; drop unknown helper hrefs before serialization.
- [x] 1.4 Implement the mandatory `Accept: application/json` Restore protocol on the existing project restore path: exact success/error envelope, `200` archived/already-active success, `404` unknown project, sanitized bounded error/retry/next fields, no raw project record, and unchanged `303 /projects/{id}` behavior for ordinary HTML/form callers; do not invent a synthetic conflict state or broad-catch infrastructure errors.

## 2. React workspace behavior

- [x] 2.1 Update `frontend/src/views/Workspace.jsx` to render summary-first project identity, capability/readiness state, canonical task counts, attention actions, and the bounded repo profile contract with safe missing-value states.
- [x] 2.2 Implement archived-project rendering: visible archived warning, Restore control, preserved history/evidence links, and no active board/launch entry point until backend state reports the project restored.
- [x] 2.3 Keep migrated board navigation in-shell through `AppLink`; keep non-migrated workflow navigation as ordinary full-page anchors; show bounded action errors without exposing raw response payloads.
- [x] 2.4 Refetch authoritative workspace and sidebar state only after Restore success; on failure keep current archived state and Restore control, show the bounded envelope error/retry link, and do not infer or rewrite capability/board/launch state.
- [x] 2.5 Update archived React-board error handling to identify archived state and link directly to `/app/projects/{project_id}` for Restore without presenting launch controls or a misleading active-board link.
- [x] 2.6 Add only the CSS/token changes required to present the new workspace sections consistently with existing Portal chrome and compact-card/readability primitives.

## 3. Regression coverage

- [x] 3.1 Extend `tests/portal/test_react_shell.py` with auth, exact top-level/nested workspace key sets, every scalar/list bound, typed malformed-value defaults, sensitive/unknown-field exclusion, unknown-project handling, and fixed board/Jinja URL ownership.
- [x] 3.2 Add Restore protocol tests for archived success, already-active idempotent success, unknown-project `404`, fixed/sanitized envelopes, preserved non-JSON form `303`, and no broad infrastructure-error conversion; also prove archived workspace and direct React-board access are restore-first and never launchable.
- [x] 3.3 Extend frontend tests with active summary/profile rendering, missing/malformed-value states, archived controls, React board-link navigation, archived-board route-back, Jinja fallback links, success-only restore refetch, failure-state preservation, and loading/error states.

## 4. Verification

- [x] 4.1 Run targeted backend and frontend workspace tests; fix failures without changing unrelated dirty-tree work.
- [x] 4.2 Run `npm --prefix frontend run check` and confirm the production build succeeds.
- [x] 4.3 Run `uv run pytest -q`, strict OpenSpec validation for `react-project-workspace-parity`, and `git diff --check`.
- [x] 4.4 Perform browser smoke coverage for `/app`, active workspace, board navigation, archived direct workspace and archived-board access, Restore success/failure behavior, and non-migrated Jinja links; record any remaining fallback behavior.
