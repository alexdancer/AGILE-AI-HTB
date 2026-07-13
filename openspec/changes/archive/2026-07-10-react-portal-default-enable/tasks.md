## 1. Lock the Landing Contract

- [x] 1.1 Replace Jinja-first routing assertions with failing build-aware tests for auth-disabled root/login/logout and auth-required successful login/authenticated root, covering both no-project and connected-project states.
- [x] 1.2 Extend missing-index and partial-build tests to prove every automatic landing uses the existing first-project or `/projects` Jinja fallback while explicit React deep links retain the clear `503` response.
- [x] 1.3 Preserve regression tests proving unauthenticated auth-required root still routes to `/login`, successful login still sets the signed cookie, and unknown `/app/*` paths remain unowned.

## 2. Enable the Build-Aware React Front Door

- [x] 2.1 Expose one dependency-light React build-readiness helper in `react_shell.py` that reuses existing index and referenced-asset validation without duplicating filesystem rules.
- [x] 2.2 Refactor the Portal landing helper to return `/app` only for a complete React build and otherwise preserve the current first-connected-project or `/projects` Jinja destination.
- [x] 2.3 Route authenticated root, successful auth-required login, auth-disabled login GET/POST, and auth-disabled logout through the shared build-aware landing helper while leaving auth-required logout at `/login`.
- [x] 2.4 Add executable direct-route checks proving existing Jinja Dashboard, project workspace/board, Sessions, Alarms, Setup, Settings, task history, reports, and Task Breakdown Review routes remain reachable, and preserve negative route-ownership checks for non-migrated `/app/*` paths.

## 3. Verify Default Promotion

- [x] 3.1 Run targeted Portal routing and React shell tests, then `uv run pytest -q`.
- [x] 3.2 Run `npm --prefix frontend run check`, strict OpenSpec validation, and `git diff --check`.
- [x] 3.3 Browser-smoke a built app from default root through React Dashboard, project workspace, and board, then follow at least one ordinary full-page Jinja fallback link; also confirm missing/partial-build default fallback remains usable.
- [x] 3.4 Run an independent final review for auth boundaries, build-gate consistency, route ownership, fallback safety, and executable test coverage before marking the change complete.
