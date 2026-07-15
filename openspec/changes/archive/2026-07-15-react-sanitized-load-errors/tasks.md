## 1. The invariant

- [x] 1.1 Add a frontend test asserting that no file in `frontend/src/views/` lets backend-derived text reach a load-error branch: no `safeError` may reference `error.message`/`error?.message`, and no JSX may interpolate it directly.
- [x] 1.2 Scope the assertion so the action-path pattern stays legal (`boundedError(outcome?.error, …)` and the `catch` branches named out of scope in design Decision 3), and comment why the two are different.
- [x] 1.3 Confirm the test fails against the current tree before any view is fixed — it must catch all five, including `Alarms.jsx:30`.

## 2. Views

- [x] 2.1 `Alarms.jsx:30` — `safeError` returns fixed strings; stop passing `error.message` through `boundedError`. Keep the existing "Alarms require sign-in." copy.
- [x] 2.2 `BudgetSettings.jsx:91` — add a `safeError` local matching the majority pattern; drop backend text from the load-error branch.
- [x] 2.3 `WorkerSettings.jsx:200` — same.
- [x] 2.4 `ControlPlaneSettings.jsx:160` — same.
- [x] 2.5 `ProjectSettings.jsx:165` — same; note its current text is bounded but still backend-derived, which design Decision 1 and the spec both reject.
- [x] 2.6 Confirm the invariant test from 1.1 now passes.

## 3. Not-found

- [x] 3.1 `App.jsx:135` — the not-found branch links to `/dashboard` instead of the `/app` alias.
- [x] 3.2 Add a frontend test that the not-found branch renders and targets a canonical URL, not `/app`.

## 4. Tests

- [x] 4.1 Add per-view tests for the five fixed views: a failed load renders the fixed message; a 401 renders the sign-in message; neither contains backend text.
- [x] 4.2 Add a test that a negotiated action outcome still surfaces the backend's authored message, so the sanitization does not regress operator guidance (spec: "Negotiated action outcomes still reach the operator").
- [x] 4.3 Mutation-check one view: restore its backend-text render and confirm both its own test and the invariant fail.

## 5. Plan

- [x] 5.1 Close slice 11a's Decision 6 in `REACT_PORTAL_PARITY_PLAN.md`, recording that load-error sanitization is now enforced by test rather than convention.
- [x] 5.2 Reviewed 11a's Decision 6 reference to `Alarms.jsx:27`: it cited that view as an example of surface-specific per-view copy, which was accurate, and did not claim the view was leak-free. No correction needed; the archived design stands.

## 6. Verification

- [x] 6.1 `openspec validate react-sanitized-load-errors --strict`.
- [x] 6.2 `npm --prefix frontend run check`.
- [x] 6.3 `uv run pytest -q` (expected unaffected; frontend-only change).
- [x] 6.4 Confirm no `error.message` remains in any view's load-error branch, and that the action-path occurrences named in the proposal are the only ones left in `frontend/src/views/`.
- [ ] 6.5 `git diff --check`, then sync and archive the change.
