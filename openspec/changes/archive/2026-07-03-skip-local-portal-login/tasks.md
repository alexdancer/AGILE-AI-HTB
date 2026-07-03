## 1. Auth mode plumbing

- [x] 1.1 Add one effective `portal_auth_required` setting/config path with default-safe behavior for direct app startup.
- [x] 1.2 In `htb serve`, infer `portal_auth_required=false` only for loopback binds when no explicit auth setting is provided.
- [x] 1.3 Keep Docker/non-loopback/shared configs auth-required unless explicitly configured otherwise.

## 2. Portal routing/auth behavior

- [x] 2.1 Update `require_portal_auth` to bypass auth only when effective portal auth is disabled.
- [x] 2.2 Update `/` and `/login` to redirect to `_default_portal_landing(...)` when auth is disabled.
- [x] 2.3 Update `/logout` to clear any cookie and return to the landing page when auth is disabled, while preserving current auth-required logout behavior.
- [x] 2.4 Hide or demote logout/login-only UI copy in no-auth mode if current templates expose it.

## 3. Docs and operator checks

- [x] 3.1 Update README/getting-started/operator docs so default local setup opens `http://localhost:8000/` without token entry.
- [x] 3.2 Keep portal-token guidance for non-loopback, hosted, reverse-proxy, Docker/shared exposure, and explicit auth-required mode.
- [x] 3.3 Update `htb check` so missing portal token is not a readiness failure when effective auth is disabled.

## 4. Tests and validation

- [x] 4.1 Add/update portal auth tests for no-auth loopback root, `/login`, protected page, and logout behavior.
- [x] 4.2 Add/update tests proving auth-required mode still rejects unauthenticated protected pages and accepts the existing signed-cookie login flow.
- [x] 4.3 Add/update CLI/operator setup tests for loopback auth inference and non-loopback auth-required behavior.
- [x] 4.4 Run `openspec validate skip-local-portal-login --strict`.
- [x] 4.5 Run `uv run pytest` after implementation because this repo requires fresh pytest verification after edits.
