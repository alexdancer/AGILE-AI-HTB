## Why

The React Portal AGILE Board's archive/history branch still exits into Jinja: archiving or dismissing a card, and following the "task history" link, drops operators out of the React shell into the server-rendered `task_history.html` page. This is the last primary Board journey that leaves React, so migrating it makes the normal governed Board loop coherent end to end before Alarms and Settings.

## What Changes

- Make the canonical authenticated `/projects/{project_id}/task-history` route build-aware: serve React when the complete frontend build exists and preserve the existing Jinja page as missing/partial-build fallback and parity oracle.
- Add an authenticated, read-only, bounded FastAPI JSON handoff for project task history: the count-bearing archive filters, and per-task description, id, lifecycle status, archive state/timestamp, estimate/actual token evidence, recommended model, session-report link, Worker Run id, blocked reason, and manual-estimate indicator. Reuse the existing `project_task_history_context` builder; no evidence visible in Jinja becomes irreversibly hidden by a React preview cap.
- Add a React Project Task History view inside the existing Portal chrome with bookmarkable archive filters that map to the canonical `?filter=` query, preserving deep-linkable/back-button behavior.
- Negotiate the existing inline **Unarchive** action (`POST /projects/{project_id}/tasks/{task_id}/unarchive`): return a JSON outcome to React callers and keep the current Jinja redirect for HTML callers. No new mutation, no new route, no schema change.
- Wire the Board's archive/history links and the workspace history handoff to the React-owned route when the build is complete, so the archive branch no longer transitions to Jinja mid-loop.
- Add no workflow mutations beyond negotiating existing Unarchive, no new archive lifecycle status, no schema change, no polling/real-time contract, and no Jinja retirement.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `react-portal-shell`: Extend build-aware canonical route ownership, authenticated bounded read-only JSON handoff, client routing, missing/partial-build Jinja fallback, shared-shell navigation, and the negotiated Unarchive action outcome to Project Task History.
- `project-task-history`: Require React presentation parity for the history page — bookmarkable archive filters, full per-task evidence and restore path, and inline Unarchive — without changing task lifecycle, archive metadata semantics, or when tasks are deleted.

## Impact

- FastAPI Portal/React route selection, the read-only history projection helper, and Unarchive content negotiation under `src/agile_ai_htb/routes/` (`portal.py`, `react_shell.py`).
- The existing `project_task_history_context` builder and `task_history.html` remain the parity source and missing-build fallback.
- React routing, sidebar active state, the Project Task History view, filter/evidence components, styling, and frontend tests under `frontend/`.
- Portal endpoint/auth/fallback/projection/negotiation tests under `tests/portal/`.
- No database migration, dependency addition, Worker Adapter behavior change, token-accounting change, or new mutation API.
