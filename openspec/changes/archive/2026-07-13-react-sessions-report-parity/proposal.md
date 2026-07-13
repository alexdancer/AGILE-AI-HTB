## Why

The React Portal currently sends operators out of the shell to Jinja for the Sessions list and Session Report, splitting the primary governance-evidence workflow. These two read-only surfaces should migrate together so operators can scan active work and inspect complete audit evidence without needing the old report.

## What Changes

- Make the canonical authenticated `/sessions` and `/sessions/{session_id}` routes build-aware: serve React when the complete frontend build exists and preserve the existing Jinja pages as missing/partial-build fallback.
- Add authenticated, read-only, bounded FastAPI JSON handoffs for the Sessions list, full Session Report, paged evidence collections, explicit full-text continuation, and lightweight report freshness metadata. Reuse the current session artifact, evidence summary, token-accounting, related Agent Review, and guardrail calculations; no evidence visible in Jinja becomes irreversibly hidden by a React preview cap.
- Add React Sessions and Session Report views inside the existing Portal chrome. Preserve compact summaries plus every current audit path: token totals/categories, Worker token components, raw provider usage, budget-zone timeline, Worker Run timeline, Repo Context Brief, Alarms, Checkpoint results, and related Agent Review evidence.
- Auto-refresh the Sessions list only while active/running sessions exist. For an active report, poll only freshness metadata; show `New session evidence available` and replace report data only after the operator explicitly refreshes.
- Keep dense/raw evidence secondary and bounded. Add no workflow mutations, schema changes, websocket transport, generalized real-time contract, or Jinja retirement.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `react-portal-shell`: Extend canonical React route ownership, authenticated bounded JSON handoffs, build-aware Jinja fallback, navigation, and polling behavior to Sessions and Session Report.
- `portal-evidence-readability`: Require React Sessions/Report information parity, compact-first presentation, complete secondary audit evidence, and explicit freshness behavior.

## Impact

- FastAPI Portal/React route selection and read-only projection helpers under `src/agile_ai_htb/routes/`.
- Existing Jinja session context builders remain the parity source and fallback implementation.
- React routing, sidebar active state, Sessions/Report views, evidence components, styling, and frontend tests under `frontend/`.
- Portal endpoint/auth/fallback/projection tests under `tests/portal/`.
- No database migration, dependency addition, Worker Adapter behavior change, token-accounting change, or mutation API change.
