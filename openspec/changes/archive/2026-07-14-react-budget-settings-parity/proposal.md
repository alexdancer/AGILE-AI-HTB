## Why

Budget Settings is the next React parity slice (Phase 5 #5) and the first of the Settings group. It is the simplest authenticated mutation surface, so it establishes the reusable "on-page mutation" pattern that Control Plane, Worker, and Project Settings will copy. Porting the current Jinja page as-is would freeze its forced `POST → 303 /setup` redirect, which discards the operator's page context — the parity plan explicitly requires React Settings mutations to stay on-page with inline outcomes.

## What Changes

- Make the canonical authenticated `/settings/budget` GET build-aware: serve React when the complete frontend build exists, and keep the existing Jinja page as missing/partial-build fallback and parity oracle.
- Add a new authenticated, bounded FastAPI JSON read for Budget Settings state (daily cap, per-session cap, today's counter used/remaining/`budget_since`, last reset timestamp) so React never recomputes budget domain values.
- Give the existing `POST /settings/budget` and `POST /settings/budget/reset` actions a sanitized, content-negotiated JSON outcome envelope (success + saved state, or sanitized validation error) for non-HTML callers, while preserving the current HTML form redirect unchanged. Raw exception text never reaches the operator.
- Add a React Budget Settings view inside the existing Portal shell chrome, on the canonical `/settings/budget` URL (no parallel `/app/*` route). It renders the save form, today's budget counter, the spend-authority reference, and the soft-reset action.
- React save/reset show inline success or sanitized error and then re-fetch authoritative budget state **without** discarding the operator's page context. Successful save does **not** force navigation to `/setup`; "Back to setup" remains an explicit link. Reset requires confirmation.

Explicit non-goals (lazy slice boundaries):

- No change to budget enforcement, cache-read exclusion, spend-authority buckets, or any token-accounting rule.
- No schema/database migration.
- No migration of Control Plane, Worker, or Project Settings, or Setup Overview — those are later separate slices.
- Do not delete the Jinja `/settings/budget` template/route; it stays as build-aware fallback until the final Jinja-retirement change.
- Desktop-only; no mobile/narrow-screen redesign.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `token-budget-setup`: the budget save and daily-counter reset actions gain a sanitized, content-negotiated JSON outcome envelope for non-HTML callers (preserving the existing HTML redirect), and the Portal exposes an authenticated bounded JSON read of current budget-setup state.
- `react-portal-shell`: React owns the build-aware `/settings/budget` surface — a Budget Settings view rendered in Portal chrome that consumes the authenticated budget JSON, negotiates the save/reset outcomes, shows inline feedback, re-fetches authoritative state without losing page context, and navigates in-shell.

## Impact

- Backend: `src/foreman_ai_hq/routes/portal.py` (`/settings/budget` GET build-aware selection; save/reset negotiated envelope), `src/foreman_ai_hq/routes/react_shell.py` (new authenticated budget-state JSON endpoint).
- Frontend: new `frontend/src/views/BudgetSettings.jsx`, routing in `frontend/src/App.jsx`, shared shell/tokens.
- Preserved: `src/foreman_ai_hq/templates/budget.html` as fallback/parity oracle; FastAPI remains authoritative for all budget domain rules.
- Tests: `tests/portal/test_react_shell.py` (route selection, JSON auth/shape, negotiated outcomes), React source/contract assertions for field names.
