## 1. Response Behavior

- [x] 1.1 Update `/settings/control-plane/test` to detect browser HTML submissions using the existing portal accept-header pattern.
- [x] 1.2 Preserve the existing JSON success and failure response shape/status for API clients.
- [x] 1.3 Return browser submissions to `/settings/control-plane` with `303 See Other` after recording success or failure status.

## 2. Settings UI

- [x] 2.1 Replace the always-visible raw connection-status dump with a concise latest-test summary on `control_plane.html`.
- [x] 2.2 Show status, checked time, provider, model, usage total when present, and sanitized error when present.
- [x] 2.3 Keep the full sanitized status details behind native `<details>` so support evidence remains available.

## 3. Tests

- [x] 3.1 Add a portal test proving browser-style success submission redirects back to `/settings/control-plane` and the page shows the updated clean result.
- [x] 3.2 Add a portal test proving browser-style failure submission redirects back to `/settings/control-plane`, shows a sanitized error, and does not leak secrets.
- [x] 3.3 Keep/adjust existing JSON tests proving API clients still receive JSON success and failure responses.

## 4. Verification

- [x] 4.1 Run targeted Control Plane portal tests.
- [x] 4.2 Run `openspec validate show-control-plane-test-result-in-ui --strict`.
- [x] 4.3 Run `uv run pytest` after implementation, unless blocked by unrelated dirty-worktree failures and reported with evidence.
