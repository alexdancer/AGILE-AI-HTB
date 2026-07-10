## Why

React now has Portal chrome, dashboard parity, and a project-scoped AGILE Board workflow, but selecting a project still opens a reduced workspace view. The React workspace omits important project identity/readiness details, encourages board access for archived projects, and sends attention links back to Jinja even when the React board can handle the workflow. Complete this project-entry surface before enabling React as the default Portal landing.

## What Changes

- Make the React project workspace equivalent to the existing Jinja project overview for the migrated project route.
- Replace the broad workspace JSON handoff with an exact authenticated projection: fixed top-level `project`, `summary`, `controls`, and `links` objects; exact nested keys; typed null/empty defaults; redaction-before-truncation; bounded strings/lists; and safe malformed-value handling.
- Render the project profile fields already available in Jinja: root path, branch, language/framework/package hints, test command, run command, and relevant docs.
- Render capability state, missing launch-readiness reasons, task counts, total tasks, and attention actions from existing FastAPI helpers.
- Make archived-project behavior explicit in React: show archive state and Restore action, preserve history/evidence links, hide active board/launch entry points until restore, and route archived React-board access back to the restore-first workspace.
- Add a mandatory `Accept: application/json` response contract to the existing project Restore POST path for React callers: fixed `200` success and `404` unknown-project envelopes with retry/next links, idempotent already-active success, and unchanged `303` behavior for ordinary HTML/form callers.
- Keep project attention links inside React when they target the migrated project board; retain ordinary full-page navigation for non-migrated Sessions, Task history, Worker setup, and Project settings pages.
- Preserve existing FastAPI authority for project lookup, capability calculation, archive/restore semantics, launch readiness, and workflow routing.
- Add backend projection-contract tests and frontend rendering/navigation tests for active, archived, missing, loading, and error states.
- Keep `/projects`, repo connection, project archive management, Jinja workspace fallback, and React default landing behavior unchanged in this change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `react-portal-shell`: extend the migrated React project workspace contract with bounded profile/readiness data, archived-project safety, and route-correct attention/workflow links.
- `project-workspace`: require the React-owned project workspace to preserve the existing project identity, readiness, action-summary, profile, and workflow-link contract while the Jinja surface remains available as fallback.

## Impact

- Frontend: `frontend/src/views/Workspace.jsx`, `frontend/src/App.jsx` only if route/link state requires adjustment, `frontend/tests/shell.test.mjs`, and shared tokens only if the existing Portal primitives cannot render the added workspace sections.
- Backend: `src/agile_ai_htb/routes/react_shell.py` workspace projection and mandatory negotiated JSON outcomes on the existing project Restore action. Existing `board_workspace` and project archive helpers remain the authority.
- Frontend archive safety may also touch `frontend/src/views/Board.jsx` only to route an archived-board response back to the React restore-first workspace.
- Tests: `tests/portal/test_react_shell.py`, project-workspace/archive regression coverage, and frontend contract tests.
- No database/schema migration, new project table, new generic mutation API, Worker Adapter/model/tracking-mode change, token-accounting change, SPA dependency, or React default-landing change.
- Jinja remains the fallback/non-migrated implementation. React default enable is a later separate change after this workspace parity gate and fresh full verification.
