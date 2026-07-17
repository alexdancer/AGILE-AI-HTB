## Why

Setup Overview is Phase 5 slice #9, the last read-only operator surface before Login. It is a router: every card on `/setup` points at a Settings destination, and all four of those destinations (`/settings/control-plane`, `/settings/budget`, `/settings/project`, `/settings/workers`) are now React-owned. Slice ordering put Setup here deliberately — migrating it now means its next-action flow stops sending operators from React back into Jinja.

The page has no mutations. `GET /setup` (`portal.py:483`) computes four readiness steps plus one next action and renders `setup.html` (56 lines). Every rule it applies — control-plane connection state, budget confirmation, adapter launchability, launch-ready project capability, and the ready/next-step derivation — already lives in existing helpers. So this slice is the smallest of the Settings group: one build-aware GET, one bounded JSON read, one React view, no negotiated outcome.

## What Changes

- Make the canonical authenticated `/setup` GET build-aware: serve React when the complete frontend build exists, keep the existing `setup.html` Jinja page as missing/partial-build fallback and parity oracle.
- Extract the readiness computation from `setup_overview` into a shared `_setup_overview_state(request)` helper in `portal.py` so the Jinja page and the React handoff render one computation rather than two copies of the step list.
- Add a new authenticated, bounded FastAPI JSON read for Setup Overview state in `react_shell.py` guarded by `require_portal_auth`, calling that shared helper. It exposes: the four `steps` (name, state, href, detail), `ready_to_launch`, `next_step` (label, href, detail), and a bounded `active_adapter` projection.
- Converge the Jinja `setup.html` tracking display onto the same `tracking.mode` view-model source React uses, replacing its raw `verification_evidence` read. Same rendered value, one source for both renderers.
- Preserve the bookmarkable `?adapter_id=` query parameter. React reads it from the URL and passes it through to the JSON read; the server keeps owning active-adapter selection via `_active_adapter_for_request`. React does not pick the adapter itself, and the URL stays copy/pasteable.
- Bound the `active_adapter` projection to an allow-list: `name`, `verification_status`, `launchable`, and tracking mode — the four fields `setup.html` renders. The full `verification_evidence` blob is not serialized. This follows the slice 7/8 discipline: operator-facing configuration in, internal detection detail out.
- Forward `adapter_id` from the Setup Worker card to `/settings/workers` so the operator lands on the adapter they were just looking at rather than the default. Slice 7's redirect defect was this exact parameter being dropped.
- Add a React Setup view inside the Portal shell on canonical `/setup` (no `/app/*` alias): next-action toolbar, four readiness cards with Open links, the launch-readiness panel, and the active Worker adapter panel.
- Reconcile the `react-portal-shell` spec now that React owns the Setup group: the landing requirement adds `/setup` to React route ownership, the chrome requirement gains a Setup highlighting scenario alongside the Sessions and Settings ones, and the two clauses that still name Setup as non-migrated full-page navigation are corrected. Spec-only; no behavior change beyond the in-shell navigation this slice delivers.

Explicit non-goals (lazy slice boundaries):

- No change to readiness rules, step derivation, or the next-action computation. React renders `steps` and `next_step`; it recomputes nothing.
- No new mutation routes; no content negotiation (the page has no actions to negotiate); no schema/database migration.
- No re-litigation of Setup readiness semantics. `require-launch-ready-project-setup` already corrected the optional-project drift at `portal.py:494`; React copies the corrected behavior and must not reintroduce the old claim.
- No migration of Login or the Portal Recovery Surface (slice 10), and no `/app` retirement (final retirement change).
- Do not delete `setup.html`; it stays as build-aware fallback until final Jinja retirement.
- Desktop-only.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `react-portal-shell`: React owns the build-aware `/setup` surface — a Setup Overview view in Portal chrome that consumes a new authenticated bounded JSON read of readiness state, preserves the bookmarkable `adapter_id` context and forwards it to Worker Settings, and navigates in-shell rather than as a full-page link.

## Impact

- Backend: `src/foreman_ai_hq/routes/portal.py` (`/setup` GET build-aware, shared `_setup_overview_state` helper), `src/foreman_ai_hq/routes/react_shell.py` (new authenticated setup-state JSON endpoint calling that helper), `src/foreman_ai_hq/templates/setup.html` (tracking source convergence).
- Frontend: new `frontend/src/views/Setup.jsx`, routing in `frontend/src/App.jsx`, Setup sidebar link becomes in-shell client navigation, `frontend/src/views/WorkerSettings.jsx` honors the forwarded `adapter_id`, shared shell/tokens.
- Preserved: FastAPI remains authoritative for every readiness rule and the next-step derivation; `setup.html` remains fallback/oracle; `/app` and its alias behavior are untouched.
- Tests: `tests/portal/test_react_shell.py` (route selection, JSON auth/shape, bounded adapter projection invariant, `adapter_id` passthrough, launch-ready-project readiness regression), React source/contract assertions for field names and route wiring.
