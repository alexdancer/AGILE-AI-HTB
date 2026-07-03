## Why

The local-first operator path currently makes a solo `htb serve` user copy a portal token before they can see the app. That protects shared hosts, but it is friction for the default loopback local version.

## What Changes

- Let default loopback local runs (`127.0.0.1` / `localhost`) open the Portal without the login page.
- Keep token auth required for non-loopback/shared binds such as `0.0.0.0`, hosted/reverse-proxy setups, or explicit secure mode.
- Redirect `/` directly to the normal project landing page when auth is not required.
- Keep `/login`, bearer-token auth, signed-cookie auth, and logout behavior for auth-required deployments and compatibility.
- Update local setup docs/copy to stop making portal token entry the default local step.

## Capabilities

### New Capabilities

- `portal-local-access`: Defines when local Portal access may skip token login and when token auth remains required.

### Modified Capabilities

- `operator-setup`: Local setup docs and readiness checks should treat portal token auth as shared-host protection, not mandatory loopback startup friction.
- `project-workspace`: Default local entry should land in the project workspace/list without an intermediate login when auth is not required.
- `public-release-onboarding`: First-run onboarding should describe no-login loopback startup while preserving token guidance for shared/hosted access.
- `docker-local-run`: Docker docs/smoke expectations should distinguish local published-port access from auth-required shared exposure.

## Impact

- Affected code: `src/agile_ai_htb/auth.py`, `src/agile_ai_htb/routes/portal.py`, `src/agile_ai_htb/cli.py`, settings/config helpers as needed.
- Affected UI/templates/docs: login/root redirects, sidebar logout visibility if auth is disabled, README/getting-started/Docker setup copy.
- Tests: portal auth tests, operator setup tests, packaging/docs assertions, Docker smoke expectations if they mention `/login`.
- No new dependency, user table, RBAC, OAuth, schema migration, or Worker Adapter change.
