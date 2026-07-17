## Why

The React `/app` shell became the default authenticated landing as soon as the frontend was built, but it lacks Portal chrome, dashboard, and full AGILE Board parity. Sending operators into a split-brain product experience — a partial `/app` island that punts back to Jinja for real workflow — premature-defaults an incomplete surface. Roll the landing back to the existing full Jinja Portal while React parity work continues in later phases.

## What Changes

- Remove the `/app`-first branch from `_default_portal_landing` so root `/`, login, and logout all land on the existing Jinja Portal (`/projects` or `/projects/{first-connected}`) regardless of whether the React build is present.
- Delete the now-unused `react_build_available()` helper from `react_shell.py` (Option A from exploration): the only caller was the premature-default branch, and Phase 6 can reintroduce a real gated helper alongside parity tests.
- `/app` and its client sub-routes remain reachable at the same URLs as an experimental/migrated surface. No server route is removed; React keeps working when built.
- No UI link to `/app` is added in this change. Discoverability of `/app` during the interim is a Phase 2 chrome concern, not a Phase 1 routing concern.
- Build fallback behavior (missing → 503, partial → 503, no blank shell) is already implemented and stays unchanged.
- Tests that asserted the `/app`-first default are flipped to assert the Jinja landing; one new regression test locks "built assets + valid cookie → Jinja landing, not `/app`" against future regressions.

**BREAKING** (behavioural, not API): authenticated root/login no longer redirect to `/app` when the React build is present. Operators who relied on `/app` as the landing must navigate to `/app` explicitly. This is intentional and temporary — Phase 6 re-enables React as default once parity gates pass.

## Capabilities

### New Capabilities
<!-- None. This change rolls back a default; it introduces no new capability. -->

### Modified Capabilities
- `react-portal-shell`: the "React shell is the default authenticated landing" requirement changes — React is no longer the default landing while parity is incomplete. The landing SHALL use the existing server-rendered Portal until a later change re-enables React after parity gates pass.

## Impact

- **Code:** `src/agile_ai_htb/routes/portal.py` (`_default_portal_landing` — remove `/app`-first branch + delete `react_build_available` import usage); `src/agile_ai_htb/routes/react_shell.py` (delete `react_build_available()` helper; all other routes/JSON/build detection stay).
- **Tests:** `tests/portal/test_react_shell.py` — flip 3 tests asserting `/app` landing to assert Jinja; add 1 regression test (built + valid cookie → Jinja).
- **Frontend:** untouched. `npm --prefix frontend run check` remains green.
- **APIs:** no JSON endpoint or route is added/removed/renamed. `/app`, `/api/projects`, `/api/projects/{id}/workspace`, `/api/projects/{id}/board` all stay.
- **References:** `docs/REACT_PORTAL_PARITY_PLAN.md` Phase 1; archived `openspec/changes/archive/2026-07-09-react-portal-front-door/` introduced the premature default being rolled back.