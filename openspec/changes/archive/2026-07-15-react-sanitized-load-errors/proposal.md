## Why

`REACT_PORTAL_PARITY_PLAN.md:331` has forbidden raw backend detail in operator-facing error UI since before slice 1. Five of thirteen React views violate it today:

- `BudgetSettings.jsx:91`, `WorkerSettings.jsx:200`, `ControlPlaneSettings.jsx:160`, and `ProjectSettings.jsx:165` render the backend's text into their load-error branch.
- `Alarms.jsx:30` looks compliant — it has a `safeError` local — but that local returns `boundedError(error.message, …)`, which truncates backend text rather than replacing it.

The rule is not the problem; the absence of enforcement is. Slice 11a noticed this drift and recorded Decision 6 to defer it, and the count has not improved in the three slices since. Worse, that decision named `Alarms.jsx:27` as an example of the established pattern — pointing the next author at the one leaky variant. A rule followed by eight views and broken by five degrades at the rate people copy the nearest example.

So the deliverable here is the invariant test. The five fixes are its first beneficiaries; the test is what stops the sixth.

## What Changes

- The five views adopt the majority pattern: a per-view `safeError` returning fixed, surface-specific strings chosen by status, never backend-derived text.
- A frontend invariant test asserts that no view renders backend-derived text in a load-error branch, so this regresses as a failing test rather than as a discovery three slices later.
- `App.jsx:135` — the not-found branch links to `/app`, the alias slice 11b removed as a link target everywhere else and the retirement change converts to a redirect. It targets `/dashboard`.
- **Not in this change**: negotiated action outcomes. `POST` handlers return deliberate, backend-sanitized text (`{"ok": false, "error": "Local Runner backend is disabled…"}`) that views correctly surface via `boundedError(outcome?.error, …)`. That is authored operator guidance, not exception leakage, and it stays.

Not breaking: no route, endpoint, schema, or backend change. Error copy changes; nothing else does.

## Capabilities

### Modified Capabilities

- `react-portal-shell`: a single requirement covering load-error sanitization for every React view, replacing per-surface scenarios that only ever constrained the surfaces each slice happened to touch. It also draws the line this codebase currently blurs: a failed JSON handoff is an exception and must never reach the operator, while a negotiated action outcome is authored guidance and must.

## Impact

- `frontend/src/views/BudgetSettings.jsx`, `WorkerSettings.jsx`, `ControlPlaneSettings.jsx`, `ProjectSettings.jsx` — add `safeError`, drop backend text from the load-error branch.
- `frontend/src/views/Alarms.jsx` — `safeError` stops passing `error.message` through.
- `frontend/src/App.jsx` — not-found branch targets `/dashboard`.
- `frontend/tests/shell.test.mjs` — per-view tests plus the invariant.
- `docs/REACT_PORTAL_PARITY_PLAN.md` — close Decision 6, and correct its reference to the leaky example.
- No backend change. `api.js` is untouched: it is correct for it to carry detail on the Error object; the views are wrong to render it.

### Out of scope

- Action-path `catch` branches that render `err.message` for network/500 failures (`Projects.jsx:62`, `Board.jsx:35`, `TaskHistory.jsx:56`). Same family, but they are the action pattern rather than the load pattern, and separating them keeps the invariant unambiguous.
- Not-found ownership (`:331`) and the `portal-quality-system` fallback scenario — both belong to the retirement change.
