## 1. Standalone recovery login page

- [x] 1.1 Rewrite `templates/login.html` without `extends "base.html"`: a complete standalone document with its own minimal inline styling, the existing brand wording, and the existing token form (same action, method, field name, `required`, `autofocus`, password type).
- [x] 1.2 Keep the page free of sidebar, navigation, project list, and logout control (design Decision 2).
- [x] 1.3 Confirm the rendered page needs no context beyond what `login_form` already passes, so it cannot query operator data; leave the `template_context.py:13-15` `/login` guard in place for the routes that still use the shared context.
- [x] 1.4 Add a test that `/login` renders without the shared chrome: no sidebar markup, no project data, no logout control, and no `base.html` inheritance.
- [x] 1.5 Add an invariant test that the login template does not extend or include any template the retirement change removes, so a future edit fails here rather than during retirement.

## 2. Failure rendering

- [x] 2.1 Replace the two `HTTPException(401, "invalid portal token")` raises in `portal.py::login` with a re-render of the standalone login page carrying a sanitized error, preserving the `401` status (design Decision 3).
- [x] 2.2 Use one identical operator-facing message for a wrong token, an empty submitted token, and an absent configured token (design Decision 4).
- [x] 2.3 Preserve the existing `secrets.compare_digest` comparison and its ordering; do not add an earlier return that could distinguish a partial match.
- [x] 2.4 Add tests: wrong token re-renders HTML with `401` and no raw JSON body; the submitted token is never reflected in the response; all three rejection causes produce the same message.
- [x] 2.5 Mutation-check the failure test: confirm it fails against the current `HTTPException` behavior before the fix, not merely passes after it.

## 3. Unchanged contracts

- [x] 3.1 Add a test that a correct token still sets the signed HttpOnly cookie and redirects to the existing build-aware landing.
- [x] 3.2 Add a test that auth-disabled `/login` still redirects to the normal landing and never renders the token form.
- [x] 3.3 Confirm `/logout` behavior is untouched in both auth modes.

## 4. Plan reversal

- [x] 4.1 Update `REACT_PORTAL_PARITY_PLAN.md` Product Direction (`:19`) and the target-end-state block (`:27-43`) so normal login is server-rendered and the Portal Recovery Surface is the login page.
- [x] 4.2 Supersede the Decision Log entry "React Login is a standalone branded screen; authenticated Portal chrome appears only after login" (`:463`) with the reversal, its reason, and its revisit condition (design Decision 1). Keep "Successful login always opens Dashboard" — that one still holds.
- [x] 4.3 Resolve the slice ledger's "Login + Portal Recovery Surface" row to this change, and state that retirement is the only remaining slice.
- [x] 4.4 Record in the plan that retirement may now delete `base.html` together with the duplicated templates.

## 5. Verification

- [x] 5.1 `openspec validate standalone-portal-recovery-login --strict`.
- [x] 5.2 `uv run pytest -q`.
- [x] 5.3 Browser smoke, build present: open `/login`, submit a wrong token and confirm a branded page with a readable error rather than a JSON body, then submit the correct token and confirm the React dashboard opens.
- [x] 5.4 Browser smoke, build absent: move `src/foreman_ai_hq/static/react/index.html` aside, confirm `/login` still renders standalone and that a correct token lands on the Jinja fallback landing.
- [x] 5.5 Retirement rehearsal: temporarily move `base.html` aside and confirm `/login` still renders. Restore it afterwards; this change does not delete it.
- [x] 5.6 `git diff --check`, then sync and archive the change.
