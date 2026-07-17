## Why

Alarms is the next React parity slice, but the current Jinja inbox is Dismiss-only: every card posts `action=continue`, even though the backend already supports typed alarm actions. Migrating it as-is would freeze that limitation into React. The parity plan requires the React Alarms inbox to expose validated, context-aware actions and Open/Resolved/All history instead. This is a port plus a deliberate, bounded product upgrade.

## What Changes

- Make the canonical authenticated `/alarms` route build-aware: serve React when the complete frontend build exists and preserve the existing Jinja page as missing/partial-build fallback and parity oracle.
- Add a new authenticated, bounded FastAPI JSON handoff for the Alarms inbox that requires Portal authentication. The existing general `/alarms` JSON route keeps its current (unauthenticated) auth boundary for API polling and is left unchanged; React uses the new authenticated endpoint.
- Compute an explicit per-alarm `available_actions` list on the backend so React never infers eligibility:
  - **Continue** (the existing `continue` resolve) for every open alarm.
  - **Raise Budget** only for budget alarms, targeting the exceeded cap key (`daily_cap_tokens` for `DAILY_CAP_EXCEEDED`, `session_cap_tokens` for `SESSION_CAP_EXCEEDED`) read from the alarm's own context; the current cap and used tokens are already carried in the alarm context.
  - **Abort Session** is explicitly out of scope for this slice.
  - Generic `adjust_guardrail` payload editing stays out of the inbox; React routes operators to Guardrail configuration.
- Add a backend positive-cap guard: `raise_budget` SHALL reject a new cap that is not strictly greater than the current cap for that key, before applying the existing merge into `session.guardrail_overrides.budget`.
- Add a React Alarms view inside the existing Portal chrome with bookmarkable **Open / Resolved / All** filters (default Open, mapped to `?filter=`). Resolved entries show the resolved action, a sanitized payload summary, `resolved_at`, and a Session Report link. Raise Budget uses preset increments (+25% / +50% / +100% of current) plus a custom value, with confirmation.
- Negotiate the existing `POST /alarms/{id}/resolve` action: return a bounded JSON outcome to React/JSON callers while preserving the current Jinja redirect for HTML callers.
- Add no new alarm schema/table/status, no change to the legacy JSON route's auth, no Abort Session, and no Jinja retirement.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `alarm-inbox`: Add backend-computed context-aware `available_actions` (Continue and budget-only Raise Budget), a backend positive-cap guard for `raise_budget`, bookmarkable Open/Resolved/All history filters that keep Resolved out of the default view, and an authenticated React data handoff (the shared resolve route keeps its existing auth boundary) — while preserving the existing dismiss-without-archive and audit behavior.
- `react-portal-shell`: Extend build-aware canonical route ownership, authenticated bounded JSON handoff, client routing, missing/partial-build Jinja fallback, shared-shell navigation, and the negotiated resolve action outcome to the Alarms inbox.

## Impact

- FastAPI Alarms route selection, a new authenticated Alarms JSON handoff, `available_actions` derivation, and the positive-cap guard under `src/agile_ai_htb/routes/alarms.py`, `src/agile_ai_htb/routes/react_shell.py`, and `src/agile_ai_htb/db.py` (`resolve_alarm`).
- The existing `alarms.html` / `alarm_card.html` remain the missing-build fallback and parity oracle.
- React routing, sidebar active state, the Alarms view, filter/action/confirmation components, styling, and frontend tests under `frontend/`.
- Portal endpoint/auth/fallback/projection/negotiation and `resolve_alarm` guard tests under `tests/`.
- No database migration, dependency addition, Worker Adapter behavior change, token-accounting change, or change to the legacy `/alarms` JSON auth boundary.
