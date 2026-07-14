## 1. Authenticated bounded JSON read

- [x] 1.1 Add an authenticated `GET /api/settings/workers` JSON endpoint in `react_shell.py` guarded by `require_portal_auth`, reusing `worker_adapter_view_models`, `active_adapter_for_request`, and `worker_setup_next_action`.
- [x] 1.2 Return a bounded per-adapter projection: id, kind, `configured`, `is_default`, `connection_type`, `tracking` + `tracking_mode_options`, `discovered_models`, approved `supported_models`, `launchable`, sanitized `diagnostics`, sanitized `verification_evidence` + `verification_diagnostic`, `model_discovery_label`; plus the selected `active_adapter_id` and the single `next_action`. Type absent optionals as `null`; never serialize raw path/exception text.

## 2. Negotiated mutation outcomes

- [x] 2.1 Extend `POST /settings/workers/{id}/configure` to return a bounded key-free JSON success envelope for `_wants_react_json` callers, preserving the HTML `303` redirect.
- [x] 2.2 Extend `POST /settings/workers/{id}/allowed-models` to return a bounded JSON success outcome and a sanitized JSON error outcome (rejected undiscovered models) for JSON callers, preserving the HTML redirect and the existing `?error=` query for HTML callers.
- [x] 2.3 Extend `POST /settings/workers/{id}/refresh-diagnostics` to return a bounded JSON success envelope and route any detection failure through a sanitized bounded error envelope (no raw path/exception) for JSON callers, preserving the HTML redirect.
- [x] 2.4 Confirm `POST /settings/workers/{id}/verify` and `POST /settings/workers/{id}/discover-models` keep their existing negotiated JSON shapes unchanged; React consumes them as-is.

## 3. Build-aware canonical route

- [x] 3.1 Make `GET /settings/workers` serve the React shell when the build validates via `_react_index()`, and render the existing Jinja `workers.html` at the same URL when the build is missing or partial.

## 4. React Worker Settings view

- [x] 4.1 Add `frontend/src/views/WorkerSettings.jsx` in shell chrome: adapter selector, per-adapter panel (connection type, tracking, readiness/next-action, diagnostics, verification evidence).
- [x] 4.2 Wire `/settings/workers` in `frontend/src/App.jsx`.
- [x] 4.3 Load from `/api/settings/workers`; render the adapter list and the single next-action.
- [x] 4.4 Set-default action (`configure`) with `Accept: application/json`; inline outcome; authoritative refetch without leaving the page.
- [x] 4.5 Discover→approve model workflow: Discover models (live), then approve a subset from `discovered_models`; the approve control offers only discovered models and is unavailable until discovery has run for that adapter.
- [x] 4.6 Live Verify and Discover actions with `Accept: application/json`, inline pass/fail + sanitized reasons, busy state while in flight, and authoritative refetch that keeps the operator on the adapter they were editing.
- [x] 4.7 Refresh-diagnostics action with inline sanitized outcome and refetch.
- [x] 4.8 Accessibility: keyboard-operable controls, explicit labels, visible focus, semantic headings, status/error announcements.

## 5. Tests

- [x] 5.1 `/api/settings/workers` requires portal auth; returns the exact bounded adapter projection; asserts no raw path/exception text appears even when detection/verification failed.
- [x] 5.2 Negotiated outcomes: JSON set-default success; JSON model-approval success + sanitized rejection (undiscovered models); JSON refresh-diagnostics success + sanitized error; and unchanged HTML redirects for all three.
- [x] 5.3 Verify/Discover JSON outcomes remain unchanged in shape (regression assertion).
- [x] 5.4 Build-aware `/settings/workers`: React when built, Jinja when missing/partial.
- [x] 5.5 React source/contract assertions: JSON field names, adapter-selector wiring, and the discovery-before-approval gate.

## 6. Verification

- [x] 6.1 `openspec validate react-worker-settings-parity --strict`
- [x] 6.2 `npm --prefix frontend run check`
- [x] 6.3 `uv run pytest tests/portal/test_react_shell.py -q` then `uv run pytest -q`
- [x] 6.4 `git diff --check`
- [x] 6.5 Browser smoke: open built `/settings/workers`, select an adapter, set default (stays on page), Discover models then approve a subset, Verify (pass/fail inline), refresh diagnostics; confirm no raw path/exception in evidence; then load missing/partial build and confirm Jinja fallback at the same URL.
