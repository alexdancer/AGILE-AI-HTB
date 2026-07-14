## 1. Backend: curated list single source (Decision A)

- [x] 1.1 Move the curated provider/model list from `control_plane.html` into one authoritative backend constant (e.g. `CURATED_CONTROL_PLANE_MODELS` in the control-plane route module).
- [x] 1.2 Update `control_plane.html` to render the dropdown from template context instead of the inline literal; behavior unchanged.

## 2. Backend: control-plane state JSON read

- [x] 2.1 Add an authenticated `/api/settings/control-plane` JSON endpoint in `react_shell.py` guarded by `require_portal_auth`, reusing existing settings + `get_execution_backend_status` computation.
- [x] 2.2 Return placeholder-only: provider, model, base_url, api_key_env, `api_key_present` bool, estimator_model, task_breakdown_model, legacy-env presence, `shadowed_settings`, curated model list, and sanitized `connection_status` with `online`/`needs_test`/`offline` state; typed `null` for absent optionals. Never serialize the key value.

## 3. Backend: negotiated + sanitized save/test outcomes

- [x] 3.1 Extend `POST /settings/control-plane` to return a bounded key-free JSON success envelope for `_wants_react_json` callers, preserving the HTML `303` redirect.
- [x] 3.2 Route the save `OSError` path through a sanitized bounded error envelope (no raw path/exception text) for JSON callers.
- [x] 3.3 Extend `POST /settings/control-plane/test` to return a bounded JSON outcome (`online`/`offline` + sanitized status) for JSON callers, preserving the HTML redirect and the existing last-saved-config test semantics.

## 4. Backend: build-aware canonical route

- [x] 4.1 Make `GET /settings/control-plane` serve the React shell when the build validates via `_react_index()`, and render the existing Jinja page at the same URL when the build is missing or partial.

## 5. Frontend: React Control Plane Settings view

- [x] 5.1 Add `frontend/src/views/ControlPlaneSettings.jsx` in shell chrome: model form, configured-connection panel, last-test panel.
- [x] 5.2 Wire `/settings/control-plane` in `frontend/src/App.jsx`.
- [x] 5.3 Provider-filtered curated dropdown (from JSON) + custom-model path; preserve an existing non-curated saved model via the custom path.
- [x] 5.4 Placeholder-only password key input, empty by default, never prefilled; blank submit keeps the existing key.
- [x] 5.5 Load from `/api/settings/control-plane`; submit save/test with `Accept: application/json`; inline outcomes; refetch authoritative state without leaving the page.
- [x] 5.6 Dirty-form guard: disable Test with a "Save before testing" hint while edits are unsaved; re-enable after a successful save (status shows `needs_test`).
- [x] 5.7 Render three-state connection status (`online`/`needs_test`/`offline`) and the env-shadow warning; do not collapse `needs_test` into `offline`.
- [x] 5.8 Accessibility: keyboard-operable controls, explicit labels, visible focus, semantic headings, status/error announcements.

## 6. Tests

- [x] 6.1 `/api/settings/control-plane` requires portal auth; returns the exact placeholder-only contract; asserts the key value appears in no field even when a real key is set.
- [x] 6.2 Connection status maps to `online`/`needs_test`/`offline` correctly (save → needs_test; failed test → offline; passed → online).
- [x] 6.3 Negotiated outcomes: JSON save success (key-free) + sanitized save error (no path leak), JSON test outcome, and unchanged HTML redirects.
- [x] 6.4 Build-aware `/settings/control-plane`: React when built, Jinja when missing/partial.
- [x] 6.5 Curated list single source: Jinja context and JSON read derive from the same constant (assert equality / no second literal).
- [x] 6.6 React source/contract assertions: JSON field names, provider-filter wiring, and the dirty-form Test-disable behavior.

## 7. Verify

- [x] 7.1 `openspec validate react-control-plane-settings-parity --strict`
- [x] 7.2 `npm --prefix frontend run check`
- [x] 7.3 `uv run pytest tests/portal/test_react_shell.py -q` then `uv run pytest -q`
- [x] 7.4 `git diff --check`
- [x] 7.5 Browser smoke: open built `/settings/control-plane`, edit model (Test disables), save (stays on page, status → needs_test), Test (online/offline), confirm key never shown; then load missing/partial build and confirm Jinja fallback at the same URL.
