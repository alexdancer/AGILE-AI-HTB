## 1. Authenticated bounded JSON read

- [x] 1.1 Add an authenticated `GET /api/settings/project` JSON endpoint in `react_shell.py` guarded by `require_portal_auth`, reusing `_local_backend`, `db.list_connected_projects` / `db.list_archived_connected_projects`, and `backend.project_capability`.
- [x] 1.2 Return a bounded projection: `local_runner_enabled`, sanitized `backend_status`, connected projects (id, name, `root_path`, sanitized `capability` state + reasons), archived projects (same projection), and the current `error`. Type absent optionals as `null`; pass capability/backend evidence through the shared evidence-safety helper; never serialize raw exception text.

## 2. Negotiated archive outcome

- [x] 2.1 Extend `POST /projects/{id}/archive` to return a bounded JSON success envelope for `_wants_react_json` callers and a sanitized JSON error outcome (block reason) when archiving is blocked, preserving the HTML `303` redirects (success → `/projects`, blocked → `/settings/project?error=`).
- [x] 2.2 Confirm `POST /settings/project/connect`, `POST /projects/{id}/restore`, and `POST /settings/project/{id}/read-only-proof` keep their existing negotiated JSON shapes unchanged; React consumes them as-is.

## 3. Build-aware canonical route

- [x] 3.1 Make `GET /settings/project` serve the React shell when the build validates via `_react_index()`, and render the existing Jinja `project.html` at the same URL when the build is missing or partial.

## 4. React Project Settings view

- [x] 4.1 Add `frontend/src/views/ProjectSettings.jsx` in shell chrome: connect-project form, Local Runner backend-status panel, connected-project list (capability state + reasons), archived-project list.
- [x] 4.2 Wire `/settings/project` in `frontend/src/App.jsx`.
- [x] 4.3 Load from `/api/settings/project`; render backend status, connected and archived projects.
- [x] 4.4 Connect action (`connect`) with `Accept: application/json`; inline outcome; authoritative refetch without leaving the page.
- [x] 4.5 Archive action (`archive`) with `Accept: application/json`; inline outcome incl. sanitized block reason; authoritative refetch.
- [x] 4.6 Restore action (`restore`) on archived projects with inline outcome and refetch.
- [x] 4.7 Read-only-proof action (live) with `Accept: application/json`, inline pass/guardrail-block outcome, busy state while in flight, and authoritative refetch.
- [x] 4.8 Accessibility: keyboard-operable controls, explicit labels, visible focus, semantic headings, status/error announcements.
- [x] 4.9 Forward the redirect-borne `?error=` block reason (from the Jinja `/projects` HTML archive caller) to `/api/settings/project` so the backend sanitizes it and React shows it instead of dropping it; clear it from the URL on the next action.
- [x] 4.10 Track the in-flight action as a single `{projectId, kind}` identity so only the invoked control shows its busy label while all controls stay disabled.

## 5. Tests

- [x] 5.1 `/api/settings/project` requires portal auth; returns the exact bounded projection; asserts no raw exception text appears when capability/backend evaluation failed.
- [x] 5.2 Negotiated archive outcome: JSON success; JSON sanitized block-reason error; and unchanged HTML redirects (success → `/projects`, blocked → `/settings/project?error=`).
- [x] 5.3 Connect/restore/read-only-proof JSON outcomes remain unchanged in shape (regression assertion).
- [x] 5.4 Build-aware `/settings/project`: React when built, Jinja when missing/partial.
- [x] 5.5 React source/contract assertions: JSON field names, route wiring, and connect/archive/restore/read-only-proof action paths.
- [x] 5.6 `/api/settings/project?error=` returns the forwarded block reason sanitized and bounded; React source forwards the param.

## 6. Settings-group spec reconciliation (spec-only)

- [x] 6.1 MODIFY `React is the build-aware default authenticated landing`: add `/settings/control-plane`, `/settings/budget`, `/settings/project`, `/settings/workers` to React route ownership, and rewrite the `Non-migrated and fallback Jinja routes remain reachable` scenario so the non-migrated clause defers to the per-surface requirements instead of naming Settings.
- [x] 6.2 MODIFY `React shell preserves the full Portal chrome`: add the `React-owned Settings routes are highlighted in the sidebar` scenario; keep the workspace/board active-marking prohibition and the full-page Settings link contract intact.

## 7. Verification

- [x] 7.1 `openspec validate react-project-settings-parity --strict`
- [x] 7.2 `npm --prefix frontend run check`
- [x] 7.3 `uv run pytest tests/portal/test_react_shell.py -q` then `uv run pytest -q`
- [x] 7.4 `git diff --check`
- [x] 7.5 Browser smoke: open built `/settings/project`, connect a project (stays on page), run read-only proof (inline outcome), archive a project then restore it; confirm no raw exception text in evidence; then load missing/partial build and confirm Jinja fallback at the same URL.
