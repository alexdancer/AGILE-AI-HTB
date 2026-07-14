## Context

Project Task History is the last primary React AGILE Board branch still rendered by Jinja. The board's Archive/Dismiss actions and the workspace "task history" link route to `GET /projects/{project_id}/task-history`, which renders `task_history.html` (a small read-only table: count-bearing archive filters, per-task status/token/evidence, archive timestamp, and an inline Unarchive form). The only mutation is the existing `POST /projects/{project_id}/tasks/{task_id}/unarchive`.

The Sessions and Task Breakdown Review parity slices established the reusable pattern this change follows:
- Canonical GET becomes build-aware: serve the React shell when `react_shell_available()` (index + referenced assets) is true, else the existing Jinja page (`portal.py` already branches on `_react_index()` for `/sessions`).
- A read-only, authenticated, bounded JSON handoff under `/api/...` reuses the existing Jinja context builder (`_project_task_history_context`) and the bounded-projection helpers in `react_shell.py` (`_bounded_text`, `_bounded_scalar`, `_optional_scalar`, `_optional_number`, `_safe_local_href`).
- The React view lives in `frontend/src/views/`, renders inside the shared `Shell`, and is registered in the client router's react-owned path matcher.

## Goals / Non-Goals

**Goals:**
- Serve React for a complete build at the canonical `/projects/{project_id}/task-history`, Jinja otherwise.
- Expose `GET /api/projects/{project_id}/task-history` returning the filter options and bounded per-task evidence that `task_history.html` shows today.
- React Project Task History view with bookmarkable `?filter=` archive filters and inline Unarchive.
- Negotiate the existing Unarchive POST: JSON outcome for React callers, unchanged redirect for HTML callers.
- Point the React board archive/history links and workspace history link at the canonical route when the build is complete.

**Non-Goals:**
- No new mutation, route family, archive lifecycle status, archive table, or schema change.
- No token-accounting change, no Worker Adapter change.
- No polling/auto-refresh (history is static; unlike Sessions there is no active-run freshness need).
- No Jinja retirement — `task_history.html` stays as fallback and parity oracle.
- No mobile/narrow-screen redesign.

## Decisions

- **Reuse `_project_task_history_context`.** The JSON endpoint calls the same builder the Jinja route uses, then projects it through the existing bounded helpers. This keeps filter counts, archive semantics, and evidence derivation single-sourced; React never recomputes archive state.
- **Endpoint shape mirrors `/api/sessions`.** `GET /api/projects/{project_id}/task-history?filter=<value>` returns `{ filters: [{label, value, count, active}], selected_filter, tasks: [ {id, description, status, archived, archived_at, estimate_tokens, actual_tokens, recommended_model, session_href, worker_run_id, blocked_reason, requires_manual_estimate} ] }`. Unknown project → 404 before any data via the existing `_ensure_project` guard. All strings bounded, redaction before truncation, `session_href` via `_safe_local_href`.
- **Unarchive negotiation over a new endpoint.** Extend the existing `project_unarchive_task` handler to content-negotiate: a React/JSON caller (Accept application/json) gets a bounded JSON outcome (e.g. `{ ok, task_id, status, archived: false }`) and drives an authoritative history re-fetch; HTML form callers keep the 303 redirect. This is the same negotiation precedent as the Task Breakdown action outcomes — no parallel `/api/.../unarchive` route.
- **Bookmarkable filters map to `?filter=`.** React reads the canonical query on load, requests the matching JSON, and writes the selected filter back to the URL so deep-link/back-button behavior matches the Jinja filter links. No new client-only filter namespace.
- **No polling.** History does not change under the operator mid-read the way an active session does; a manual re-fetch after Unarchive is sufficient. This deliberately does not adopt the Sessions freshness contract.

## Risks / Trade-offs

- **Content-negotiating an existing form route** risks regressing the HTML redirect. Mitigation: keep redirect as the default branch; only return JSON when the caller explicitly requests it; add a test asserting the HTML caller still gets the 303.
- **Projection drift** from the Jinja table (a field silently dropped). Mitigation: a source/contract test asserts every `task_history.html` evidence field has a JSON key, and the React view renders each.
- **Filter-count authority**: counts must come from the shared builder, not a React recount, or archived/active totals could disagree with Jinja. Mitigation: counts are pass-through from `_project_task_history_context`.
