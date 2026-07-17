## Why

Worker Settings is Phase 5 slice #7, the third Settings surface after Budget and Control Plane. It is the most complex Settings surface: multiple Worker adapters, adapter selection, a discover→approve model workflow, and two live actions (Verify, Discover models). The domain rules — adapter readiness, tracking modes, model discovery, discovered-vs-approved allow-listing, live verification — are already specified in `worker-adapter-verification`, `native-worker-model-discovery`, and `guided-worker-setup`, so this slice is largely transport plus a bounded JSON read and negotiated outcomes for the three redirect-only mutations.

## What Changes

- Make the canonical authenticated `/settings/workers` GET build-aware: serve React when the complete frontend build exists, keep the existing `workers.html` Jinja page as missing/partial-build fallback and parity oracle.
- Add a new authenticated, bounded FastAPI JSON read for Worker Settings state. The projection reuses `worker_adapter_view_models` + `active_adapter_for_request` + `worker_setup_next_action` and is sanitized through `safe_evidence`. It exposes the adapter list (id, kind, `configured`, `is_default`, `connection_type`, tracking modes + view options, `discovered_models`, approved `supported_models`, `launchable`, sanitized `diagnostics`, sanitized `verification_evidence`/`verification_diagnostic`, `model_discovery` label), the selected active adapter id, and the next-action. Absent optionals are typed `null`; raw exception/path text is never serialized.
- Give the three currently redirect-only mutations — `POST /settings/workers/{id}/configure` (set default), `POST /settings/workers/{id}/allowed-models` (approve discovered models), `POST /settings/workers/{id}/refresh-diagnostics` — a sanitized, content-negotiated bounded JSON outcome for React/JSON callers while preserving the existing HTML `303` redirects.
- Keep the two live actions — `POST /settings/workers/{id}/verify` and `POST /settings/workers/{id}/discover-models` — exactly as they are: they already negotiate JSON and return their bounded `{passed, ..., reasons, evidence}` shapes. React consumes those unchanged.
- Add a React Worker Settings view inside the Portal shell on canonical `/settings/workers` (no `/app/*` alias): adapter selector, per-adapter panels (connection type, tracking, readiness/next-action, diagnostics, verification evidence), set-default action, the discover→approve model workflow (approve gated behind prior discovery), live Verify and Discover-models actions with inline sanitized outcomes, and refresh-diagnostics.
- React actions show inline outcomes and re-fetch authoritative state without leaving the page; the adapter selection is preserved across a refetch.

Explicit non-goals (lazy slice boundaries):

- No change to how adapters are stored, discovered, verified, or how tracking authority is decided.
- No new mutation routes; no schema/database migration.
- No migration of Control Plane, Budget, or Project Settings, or Setup Overview (those are separate slices).
- Do not delete `workers.html`; it stays as build-aware fallback until final Jinja retirement.
- Desktop-only.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `react-portal-shell`: React owns the build-aware `/settings/workers` surface — a Worker Settings view in Portal chrome that consumes a new authenticated bounded JSON read of adapter state, negotiates the three redirect-only mutation outcomes, consumes the existing live Verify/Discover JSON outcomes, and re-fetches authoritative state without losing adapter-selection context.

## Impact

- Backend: `src/foreman_ai_hq/routes/portal.py` (`/settings/workers` GET build-aware; `configure`/`allowed-models`/`refresh-diagnostics` negotiated + sanitized envelope), `src/foreman_ai_hq/routes/react_shell.py` (new authenticated worker-settings-state JSON endpoint reusing `worker_setup_view` builders).
- Frontend: new `frontend/src/views/WorkerSettings.jsx`, routing in `frontend/src/App.jsx`, shared shell/tokens.
- Preserved: FastAPI remains authoritative for adapter config, model discovery, allow-listing, and live verification; `workers.html` remains fallback/oracle; Verify and Discover-models JSON contracts are unchanged.
- Tests: `tests/portal/test_react_shell.py` (route selection, JSON auth/shape, sanitization invariant, negotiated outcomes for the three redirect-only mutations), React source/contract assertions for field names and the discovery-before-approval gate.
