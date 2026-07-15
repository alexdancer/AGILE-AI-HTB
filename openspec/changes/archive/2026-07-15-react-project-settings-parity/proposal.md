## Why

Project Settings is Phase 5 slice #8, the fourth and final destination Settings surface before Setup Overview. It is the remaining pure-Jinja project surface (`/settings/project` → `project.html`): connect a local repo, view Local Runner backend status, inspect each connected project's launch capability, run a read-only launch proof, and archive/restore connected projects. The domain rules — project connection, capability evaluation, archive/restore, read-only proof launch — are already specified in `project-workspace`, so this slice is transport plus a bounded JSON read and one negotiated outcome.

## What Changes

- Make the canonical authenticated `/settings/project` GET build-aware: serve React when the complete frontend build exists, keep the existing `project.html` Jinja page as missing/partial-build fallback and parity oracle.
- Add a new authenticated, bounded FastAPI JSON read for Project Settings state in `react_shell.py` guarded by `require_portal_auth`, reusing the existing `_local_backend` + `project_capability` + connected/archived project listings. It exposes: `local_runner_enabled`, sanitized `backend_status`, connected projects (id, name, `root_path`, sanitized `capability` with state + reasons), archived projects (same projection), and the current `error`. `root_path` is intentionally surfaced — it is the operator's own repo path shown deliberately in the Jinja page — while capability/backend evidence is bounded. Absent optionals are typed `null`.
- Give `POST /projects/{project_id}/archive` a sanitized, content-negotiated bounded JSON outcome for React/JSON callers while preserving the existing HTML `303` redirects (including the `/settings/project?error=` block-reason redirect for HTML callers).
- Keep the already-negotiating actions unchanged: `POST /settings/project/connect` (returns `{project}`/`{detail}`), `POST /projects/{project_id}/restore` (returns the React restore outcome), and `POST /settings/project/{project_id}/read-only-proof` (JSON live launch outcome). React consumes those as-is.
- Add a React Project Settings view inside the Portal shell on canonical `/settings/project` (no `/app/*` alias): connect-project form, Local Runner backend-status panel, connected-project list with per-project capability, read-only-proof action, and archive; archived-project list with restore.
- React actions show inline outcomes and re-fetch authoritative state without leaving the page.
- Reconcile the `react-portal-shell` route-ownership enumeration now that this slice completes the Settings group: the landing requirement names the four canonical Settings routes as React-owned, its non-migrated clause defers to the per-surface requirements instead of re-enumerating surfaces, and the chrome requirement gains the previously unspecified Settings sidebar-highlighting scenario. Spec-only; no behavior change.

Explicit non-goals (lazy slice boundaries):

- No change to how projects are connected, evaluated, archived/restored, or how the read-only proof is launched.
- No new mutation routes; no schema/database migration.
- No migration of the `/projects` list, `/projects/{id}` workspace, or Setup Overview (separate slices).
- Do not delete `project.html`; it stays as build-aware fallback until final Jinja retirement.
- Desktop-only.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `react-portal-shell`: React owns the build-aware `/settings/project` surface — a Project Settings view in Portal chrome that consumes a new authenticated bounded JSON read of project-connection state, negotiates the archive outcome, consumes the existing connect/restore/read-only-proof JSON outcomes, and re-fetches authoritative state without losing page context.

## Impact

- Backend: `src/foreman_ai_hq/routes/portal.py` (`/settings/project` GET build-aware; `archive` negotiated + sanitized envelope), `src/foreman_ai_hq/routes/react_shell.py` (new authenticated project-settings-state JSON endpoint reusing the existing backend/capability builders).
- Frontend: new `frontend/src/views/ProjectSettings.jsx`, routing in `frontend/src/App.jsx`, shared shell/tokens.
- Preserved: FastAPI remains authoritative for project connection, capability evaluation, archive/restore, and the read-only proof launch; `project.html` remains fallback/oracle; connect/restore/read-only-proof JSON contracts are unchanged.
- Tests: `tests/portal/test_react_shell.py` (route selection, JSON auth/shape, sanitization invariant, negotiated archive outcome), React source/contract assertions for field names and route wiring.
