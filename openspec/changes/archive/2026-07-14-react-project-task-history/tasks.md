## 1. Backend: bounded read-only history JSON

- [x] 1.1 Add `GET /api/projects/{project_id}/task-history` in `react_shell.py`, guarded by `require_portal_auth`, that calls the existing `_project_task_history_context` builder for the requested `?filter=` value.
- [x] 1.2 Return 404 for an unknown project (reuse `_ensure_project`) before serving any task data.
- [x] 1.3 Project the context through the existing bounded helpers: `filters` (label/value/count/active), `selected_filter`, and per-task `id`, `description`, `status`, `archived`, `archived_at`, `estimate_tokens`, `actual_tokens`, `recommended_model`, `session_href` (via `_safe_local_href`), `worker_run_id`, `blocked_reason`, `requires_manual_estimate`. Redact before truncating; bound every string.

## 2. Backend: build-aware canonical route + Unarchive negotiation

- [x] 2.1 Make `GET /projects/{project_id}/task-history` in `portal.py` build-aware: serve the React shell when the complete build is available (same `_react_index()`/`react_shell_available()` branch as `/sessions`), else the existing `task_history.html`.
- [x] 2.2 Register the canonical `/projects/{project_id}/task-history` path in the React shell route selection so React client routing owns it.
- [x] 2.3 Content-negotiate `POST /projects/{project_id}/tasks/{task_id}/unarchive`: return a bounded JSON outcome (`ok`, `task_id`, `status`, `archived: false`) for JSON/`Accept: application/json` callers; keep the existing 303 redirect for HTML form callers. No new route, mutation, or schema change.

## 3. Frontend: React Project Task History view

- [x] 3.1 Add `frontend/src/views/TaskHistory.jsx` rendered inside the shared `Shell`, fetching `/api/projects/{project_id}/task-history?filter=<value>`.
- [x] 3.2 Add the canonical `/projects/{project_id}/task-history` path to the client router's react-owned path matcher and route to the new view.
- [x] 3.3 Render bookmarkable archive filters that write the selected filter to the canonical `?filter=` query and re-fetch; restore the filter from the URL on load.
- [x] 3.4 Render the per-task table with parity to `task_history.html`: description/id, status pill + Archived indicator, estimate/actual/model tokens, session report link, Worker Run id, blocked reason, manual-estimate indicator, and archive timestamp.
- [x] 3.5 Add inline Unarchive for archived tasks that posts the existing action with a JSON Accept header and re-fetches authoritative history state on success.
- [x] 3.6 Point the React board Archive/Dismiss/history links and the workspace history link at the canonical `/projects/{project_id}/task-history` route.
- [x] 3.7 Practical accessibility: keyboard-operable filters and Unarchive, labeled controls, visible focus, semantic table headings, and a status announcement after Unarchive.

## 4. Tests

- [x] 4.1 Backend: history JSON requires Portal auth, returns 404 for unknown project, echoes selected filter, and includes every evidence field.
- [x] 4.2 Backend: canonical route serves React on complete build and Jinja on missing/partial build.
- [x] 4.3 Backend: Unarchive returns JSON outcome for JSON callers and preserves the 303 redirect for HTML callers, with lifecycle status unchanged.
- [x] 4.4 Frontend source/contract test: no stale field names, every `task_history.html` evidence field is rendered, filter maps to `?filter=`, Unarchive uses the existing action path.
- [x] 4.5 `npm --prefix frontend run check`.

## 5. Verification

- [x] 5.1 `openspec validate react-project-task-history --strict`.
- [x] 5.2 `uv run pytest tests/portal/test_react_shell.py -q` and `uv run pytest -q`.
- [x] 5.3 `git diff --check`.
- [x] 5.4 Browser smoke: open a project's task history with a complete build → React renders inside chrome; switch filter (bookmarkable); Unarchive an archived task and confirm authoritative refresh; confirm missing-build fallback serves Jinja.
