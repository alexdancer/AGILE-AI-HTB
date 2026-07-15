## Context

Eleven slices established one pattern: a canonical GET serves React when the build is complete, and the existing Jinja page when it is not. Login is the last surface, and the pattern does not transfer to it.

Every prior slice's Jinja page is a temporary fallback that retirement deletes. Login's is permanent — it is how an operator gets in when the build is missing, which is exactly when React cannot help. `_MISSING_BUILD_HTML` (`react_shell.py:48`) already demonstrates the shape a recovery surface takes: a self-contained inline document with no template inheritance, deliberately independent of everything it might have to apologize for.

Current state:

- `login.html` extends `base.html`. `template_context.py:13-15` special-cases `/login` to blank `sidebar_projects` with the comment "The login page must not query or expose project sidebar data before portal auth succeeds." The guard works; the inheritance is the problem.
- `base.html` carries the sidebar markup and every design token in one inline `<style>` block. 15 of 17 templates extend it.
- `POST /login` raises `HTTPException(401, "invalid portal token")`. Verified response: `401 application/json {"detail":"invalid portal token"}`.

## Goals / Non-Goals

**Goals:**

- The login page renders standalone and branded, and depends on nothing retirement deletes.
- A failed login tells the operator what to do, without revealing why it failed.
- Retirement becomes a deletion, not a rescue: remove `base.html` and 14 templates, keep one login.

**Non-Goals:**

- A React login view. This change deliberately reverses that plan decision (Decision 1).
- Deleting any template — retirement owns that.
- Not-found ownership; rate limiting; lockout; any change to authentication strength.
- Visual redesign beyond what standalone rendering requires.

## Decisions

### 1. Normal login stays server-rendered; the plan decision is reversed

The plan says React owns login (`:19`, `:463`) with server rendering as fallback. Rejected, for two reasons that only became visible after slices 11a/11b.

*It cannot be one implementation.* The plan itself requires a server-rendered login for the missing-build case (`:19`, `:42`). So React login means two login implementations permanently — unlike every other slice, where duplication ends at retirement. The coherence claim "React owns every normal user-facing route" is unachievable at login by construction.

*It buys nothing observable.* The plan's stated goal for React login is a standalone branded screen without Portal navigation (`:327`). That is what this change builds, server-rendered. The operator types a token and lands in the React dashboard either way; the renderer of a one-field form is not a product-visible fact.

No spec asserted React login — `react-portal-shell` only ever specified where a successful login *lands*, and this change leaves that build-aware target alone. The reversal is therefore a plan-doc correction, recorded with its reason, not a spec rewrite.

Revisit if login grows: multi-user, SSO, password reset, or session management would each give React something real to own.

### 2. The recovery surface is self-contained, not chrome-with-an-empty-sidebar

`login.html` could keep extending `base.html` and simply hide the sidebar. Rejected: it preserves the dependency, and retirement would have to keep `base.html` alive to serve one form — the exact chrome retirement exists to remove. It would also keep the `template_context.py` path guard load-bearing, where a future edit to the shared context could leak project data onto an unauthenticated page.

Instead the login template carries its own minimal inline styling and inherits nothing, following `_MISSING_BUILD_HTML`. Some token/style duplication between it and the React build is accepted deliberately: the recovery surface's whole job is to work when the rest does not, which means it cannot share machinery with the thing that might be broken. Its independence is the feature.

### 3. Failure re-renders the form; no JSON, no JS

Three options for reporting a bad token:

| Option | Cost |
|---|---|
| Re-render the form with an error | One template branch. No JS. Works with the build missing. |
| Negotiate JSON on `POST /login` | Matches the other 27 negotiation sites — but only helps a fetch caller, and the recovery surface has no JS to fetch with. |
| Redirect to `/login?error=1` | Puts failure state in a URL that can be bookmarked and re-shown out of context. |

Chose re-render. The recovery surface must work when JavaScript never loads, which rules out the negotiated path as this page's mechanism. The status code stays `401`.

### 4. One error message for every rejection cause

`portal.py` currently rejects an empty configured token, an empty submitted token, and a mismatched token through the same 401. That indistinguishability is worth keeping deliberately rather than by accident: a message that says "no token is configured on this server" tells an unauthenticated visitor about the deployment. The spec pins one message for all three causes, and pins that the constant-time comparison stays.

## Risks / Trade-offs

- **The recovery login's styling drifts from the React build's** → Accepted, and intended. Sharing a stylesheet would recreate the dependency this change removes. The page is small and shown rarely; drift in a token form's exact shade is not a defect.
- **Reversing a Decision Log entry sets a precedent** → Mitigated by recording it as an explicit supersession with its reason and its revisit condition, in the same log. A decision made before eleven slices of evidence is allowed to lose to the evidence.
- **A future edit re-adds `extends "base.html"`** → The spec's retirement scenario and an invariant test make that a failing test rather than a discovery during retirement.
- **Someone reads "login stays Jinja" as "the migration is incomplete"** → The plan text has to state the reasoning, not just the outcome, or this looks like an unfinished slice forever.

## Migration Plan

No data migration, no route change, no schema. Rollback is reverting the template and the route branch; the URL, form contract, and cookie behavior are untouched throughout.

## Open Questions

None blocking. Not-found ownership (`:331`) is real and unspecified, but it is a separate decision and this change does not depend on it.
