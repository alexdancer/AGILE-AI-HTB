## 1. Authenticated bounded JSON read

- [x] 1.0 Extract the readiness computation from `setup_overview` into a shared `_setup_overview_state(request)` helper in `portal.py` returning steps, `ready_to_launch`, `next_step`, active adapter, and budget settings. Both renderers call it; neither reimplements it.
- [x] 1.1 Add an authenticated `GET /api/setup` JSON endpoint in `react_shell.py` guarded by `require_portal_auth`, calling `_setup_overview_state`.
- [x] 1.2 Return a bounded projection: `steps` (name, state, href, detail), `ready_to_launch`, `next_step` (label, href, detail), and `active_adapter`. Type absent optionals as `null`; never derive readiness in the response beyond what the existing helpers compute.
- [x] 1.3 Project `active_adapter` to an allow-list: `name`, `verification_status`, `launchable`, and `tracking_mode` sourced from the view model's `tracking.mode`. Do not serialize `verification_evidence`.
- [x] 1.4 Pass `request.query_params.get("adapter_id")` to `_active_adapter_for_request` so the existing selection rule and its absent/unknown fallback stay authoritative.
- [x] 1.5 Add the Worker card's `href` with `adapter_id` forwarded to `/settings/workers` when an adapter is in effect.

## 2. Build-aware canonical route

- [x] 2.1 Make `GET /setup` serve the React shell when the build validates via `_react_index()`, and render the existing Jinja `setup.html` at the same URL when the build is missing or partial. Preserve the `adapter_id` query parameter on both paths.
- [x] 2.2 Check `_react_index()` before computing readiness so a React load does not pay for a discarded Jinja render, matching the existing Settings routes.
- [x] 2.3 Converge `setup.html` tracking onto `active_adapter.tracking.mode`, replacing the raw `verification_evidence` read. Same rendered value; one source for both renderers.

## 3. React Setup Overview view

- [x] 3.1 Add `frontend/src/views/Setup.jsx` in shell chrome: next-action toolbar, four readiness cards with Open links, launch-readiness panel, and active Worker adapter panel.
- [x] 3.2 Wire `/setup` in `frontend/src/App.jsx`.
- [x] 3.3 Load from `/api/setup`, passing through `adapter_id` from the URL when present; render `steps` and `next_step` as returned without recomputing readiness.
- [x] 3.4 Render the tracking mode, defaulting to an explicit unverified state. The view model already resolves absent modes to `"unverified"`, so this is defensive rather than a contract promise.
- [x] 3.7 Make `WorkerSettings.jsx` honor the `adapter_id` forwarded from Setup so the destination opens the adapter the operator was inspecting.
- [x] 3.8 Sanitize the load-failure notice with the established `safeError` pattern; never render raw error text into the page.
- [x] 3.5 Make the sidebar Setup link in-shell client navigation and highlight the `First-run setup` item on `/setup`.
- [x] 3.6 Accessibility: keyboard-operable controls, explicit labels, visible focus, semantic headings, status announcements.

## 4. Tests

- [x] 4.1 `/api/setup` requires portal auth; returns the exact bounded projection.
- [x] 4.2 `active_adapter` projection is allow-listed: asserts `verification_evidence` is absent and `tracking_mode` comes from `tracking.mode`.
- [x] 4.3 `adapter_id` passthrough: a supplied id selects that adapter; an absent or unknown id uses the existing fallback; the Worker card href carries the id forward.
- [x] 4.4 Readiness regression: `ready_to_launch` is false and the projects step is not ready when no Connected Project is launch-ready, even with control plane, budget, and adapter ready.
- [x] 4.5 Build-aware `/setup`: React when built, Jinja when missing/partial.
- [x] 4.6 React source/contract assertions: JSON field names, route wiring, and `adapter_id` passthrough.
- [x] 4.7 Both renderers agree on tracking: the Jinja fallback renders the view-model tracking value, and an unverified adapter reads unverified on that path.
- [x] 4.8 Sidebar highlighting on `/setup` is exclusive: no Dashboard, project, Sessions, or Settings entry is marked active.
- [x] 4.9 Mounted Setup view renders backend steps, the ready/not-ready branches, the forwarded adapter link, and a sanitized load-failure notice.

## 5. Setup-group spec reconciliation (spec-only)

- [x] 5.1 MODIFY `React is the build-aware default authenticated landing`: add `/setup` to React route ownership and remove Setup from the `Non-migrated and fallback Jinja routes remain reachable` scenario.
- [x] 5.2 MODIFY `React shell preserves the full Portal chrome`: add the `Setup route is highlighted in the sidebar` scenario and remove Setup from the full-page-navigation scenario; keep the project/board active-marking prohibition intact.

## 6. Verification

- [x] 6.1 `openspec validate react-setup-overview-parity --strict`
- [x] 6.2 `npm --prefix frontend run check`
- [x] 6.3 `uv run pytest tests/portal/test_react_shell.py -q` then `uv run pytest -q`
- [x] 6.4 `git diff --check`
- [x] 6.5 Browser smoke: open built `/setup`, confirm the four cards and next action match the Jinja page for the same state; open with `?adapter_id=` and confirm the adapter panel and the forwarded Worker link; follow each card to its React Settings destination and back in-shell; then load missing/partial build and confirm Jinja fallback at the same URL.
