## Context

`htb init` writes a portal token, `htb serve` defaults to `127.0.0.1`, `/` redirects to `/login`, and every portal page depends on `require_portal_auth`. That is safe for shared access, but noisy for the default local loopback app.

The useful split is not "local product has no auth forever". It is: loopback-only operator run can skip the token gate; shared/non-loopback access keeps the existing token gate.

## Goals / Non-Goals

**Goals:**

- Make default `htb serve` loopback access open the Portal without token entry.
- Keep token auth for non-loopback binds, hosted/reverse-proxy setups, Docker/shared exposure, and explicit auth-required config.
- Preserve existing bearer-token, signed-cookie, login, and logout code paths for auth-required mode.
- Update docs/tests so local quickstart opens the product, not the login chore.

**Non-Goals:**

- No user accounts, RBAC, OAuth, password flow, or session store.
- No schema migration.
- No Worker Adapter, token-budget, model, or project-workspace rewrite.
- No request-Host-based trust decision; Host headers are too easy to spoof.

## Decisions

### Use one auth-required setting

Add or reuse one effective setting, `portal_auth_required`, and let `require_portal_auth` return immediately when false.

Alternative considered: remove `Depends(require_portal_auth)` from every route. Rejected: many edits, easy misses, worse shared-host safety.

### Infer CLI default from bind host

When `htb serve` starts and no explicit auth setting exists, infer:

- `127.0.0.1`, `localhost`, `::1` => auth not required.
- `0.0.0.0`, `::`, public/private LAN IP, proxy/hosted config => auth required.

Alternative considered: check each incoming request client IP. Rejected: proxy behavior and Docker networking make it less predictable; bind config is simpler.

### Keep `/login` as compatibility path

If auth is disabled, `/` and `/login` redirect to the normal portal landing (`/projects` or most recent project). If auth is required, current login behavior stays.

Alternative considered: delete login page locally. Rejected: auth-required deployments and old docs/tests still need it.

### Keep Docker conservative

Docker remains auth-required by default unless the operator explicitly opts out or binds only to loopback with clear local-only docs. Container port publishing can become shared accidentally, so Docker should not silently inherit the no-login loopback assumption from inside-container `0.0.0.0`.

## Risks / Trade-offs

- Operator exposes no-login portal on a LAN -> Mitigation: auth-required remains default for non-loopback binds and Docker/shared docs name the risk.
- Tests assume `/login` first -> Mitigation: update auth tests to cover both modes.
- Docs lose token guidance -> Mitigation: keep token section for shared/hosted/Docker access, just remove it from default loopback happy path.
