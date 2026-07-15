## Why

Slices 11a and 11b put every canonical Portal URL on build-aware React, leaving one slice before the Jinja retirement: Login and the Portal Recovery Surface. The plan scoped that slice as "migrate login to React, keep minimal server rendering as fallback" (`REACT_PORTAL_PARITY_PLAN.md:19`, `:463`).

Two things make that scoping wrong, and both are only visible now that the surrounding work is done:

- **Login is the one surface whose Jinja twin never dies.** Every other slice paid duplication as a migration cost that retirement refunds by deleting the template. Login's server-rendered form must survive retirement — it is the only way in when the React build cannot load. Migrating login to React does not replace an implementation; it permanently adds a second one.
- **The branded standalone login the plan wants needs no React.** The goal (`:327`) is "a standalone branded layout without authenticated Portal navigation." That is a description of a finished recovery surface. An operator who types a token into a branded form and lands in the React dashboard cannot tell which renderer drew the form.

Meanwhile the recovery surface is not actually finished, and two real defects are waiting for whoever does retirement:

- `login.html` extends `base.html`, so it depends on the chrome — sidebar markup, layout, and every design token, all inline in that template — that retirement deletes. "Preserves only the Portal Recovery Surface" is not currently possible: 15 of 17 templates extend `base.html`, and keeping it alive for one form defeats the retirement.
- A wrong token returns `401 application/json {"detail":"invalid portal token"}` rendered raw in the browser (`portal.py:293-296`). Login is the only mutation in the Portal that never learned to report failure to a human.

This change finishes the recovery surface and drops the React login. Retirement then deletes `base.html` and 14 templates and keeps one self-contained login.

## What Changes

- `login.html` becomes a self-contained, branded, chrome-less page: its own minimal inline styling, no `extends "base.html"`, no sidebar, no navigation, no dependency on any template retirement will delete.
- A failed `/login` renders the login page again with a sanitized, non-enumerating error instead of returning a raw `401` JSON body. Status codes and the existing constant-time token comparison are unchanged.
- The successful login, auth-disabled redirect, logout, and cookie contracts are untouched. This change adds no client-side JavaScript and no JSON negotiation to `/login`.
- **Plan reversal**: `REACT_PORTAL_PARITY_PLAN.md` records that normal login stays server-rendered, superseding the Product Direction (`:19`) and Decision Log (`:463`) statements that React owns login. The slice ledger's "Login + Portal Recovery Surface" row resolves to this change. No spec asserted React login, so no spec is reversed.

Not breaking: `/login` keeps its URL, method, form field, status codes, cookie, and redirect targets. Only the failure rendering and the page's template dependency change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `portal-local-access`: the login route gains a rendering contract — standalone and independent of the shared Jinja chrome, so it survives Jinja retirement — and a failure contract that renders a sanitized error to the operator rather than a raw exception body.

## Impact

- `src/foreman_ai_hq/templates/login.html` — self-contained, branded, no `base.html`.
- `src/foreman_ai_hq/routes/portal.py` — `login` re-renders with an error instead of raising `HTTPException(401)`; `login_form` unchanged.
- `docs/REACT_PORTAL_PARITY_PLAN.md` — Product Direction, Decision Log reversal, slice ledger.
- `tests/portal/` — login failure rendering, and an invariant that the recovery login does not depend on the retiring chrome.
- No schema change, no new routes, no React change, no new dependency. `frontend/` is untouched.

### Out of scope

- Deleting `base.html` or any Jinja template — the final retirement change owns that, and this change is what unblocks it.
- Not-found ownership. `REACT_PORTAL_PARITY_PLAN.md:331` says React owns branded not-found once loaded, but FastAPI's `404` never reaches the shell. Real, unspecified, and a separate decision.
- Login features that would justify React later: multi-user, SSO, password reset, session management. If login grows past one token field, revisit this reversal.
- Rate limiting, lockout, or any change to authentication strength.
