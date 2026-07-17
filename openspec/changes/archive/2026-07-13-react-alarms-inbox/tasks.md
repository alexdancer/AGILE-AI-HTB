## 1. Backend: available_actions + positive-cap guard

- [x] 1.1 Add a backend helper that computes `available_actions` per alarm: `continue` for every open alarm; `raise_budget` `{action, cap_key, current_cap}` only for `DAILY_CAP_EXCEEDED` (`daily_cap_tokens`) and `SESSION_CAP_EXCEEDED` (`session_cap_tokens`), reading the current cap from the alarm context. Never emit `abort_session` or `adjust_guardrail`.
- [x] 1.2 Add a positive-cap guard in `db.resolve_alarm`: when `action == "raise_budget"`, read the current cap for the payload's cap key from `session.guardrail_overrides.budget` and raise a client error if the new value is not strictly greater; leave budget unchanged and alarm open on rejection.

## 2. Backend: authenticated JSON handoff + route selection + negotiation

- [x] 2.1 Add `GET /api/alarms?filter=open|resolved|all` guarded by `require_portal_auth`, mapping filter to `db.list_alarms(resolved=...)` (open→False, resolved→True, all→none).
- [x] 2.2 Project the response through the existing bounded helpers: `filters` (label/value/selected), `selected_filter`, and per-alarm `id`, `type`, `severity`, `session_id`, `session_href` (via `_safe_local_href`), bounded `context`, `recommended_action`, `available_actions`, and for resolved alarms `resolved_action`, sanitized `resolved_payload_summary`, `resolved_at`. Redact before truncating.
- [x] 2.3 Make `GET /alarms` build-aware: serve the React shell when the complete build is available (same `_react_index()`/`react_shell_available()` branch as `/sessions`), else render the existing `alarms.html`. Register `/alarms` in the React shell route selection so client routing owns it.
- [x] 2.4 Content-negotiate `POST /alarms/{alarm_id}/resolve`: return a bounded JSON outcome for JSON callers (including a sanitized error outcome envelope when the positive-cap guard rejects); preserve the existing 303 redirect to `/alarms` for HTML callers. Leave the legacy open `/alarms` JSON route and its auth unchanged.

## 3. Frontend: React Alarms view

- [x] 3.1 Add `frontend/src/views/Alarms.jsx` rendered inside the shared `Shell`, fetching `/api/alarms?filter=<value>`.
- [x] 3.2 Add the canonical `/alarms` path to the client router's react-owned path matcher and route to the new view.
- [x] 3.3 Render bookmarkable Open/Resolved/All filters (default Open) that write the selected filter to the canonical `?filter=` query and re-fetch; restore from the URL on load.
- [x] 3.4 Render each open alarm from `available_actions`: Continue button always; Raise Budget only when present, with presets (+25%/+50%/+100% of `current_cap`) plus a custom value and a confirmation step.
- [x] 3.5 Render Resolved rows with resolved action, sanitized payload summary, `resolved_at`, and Session Report link; link to Guardrail configuration for generic guardrail changes.
- [x] 3.6 Submit resolve actions with a JSON Accept header; on success re-fetch authoritative inbox state; on sanitized rejection keep the alarm shown with an inline error.
- [x] 3.7 Point the sidebar/nav Alarms link at the canonical `/alarms` route.
- [x] 3.8 Practical accessibility: keyboard-operable filters/actions, labeled controls, visible focus, semantic headings, confirmation-dialog focus handling, and a status announcement after resolve.

## 4. Tests

- [x] 4.1 Backend: `/api/alarms` requires Portal auth, echoes selected filter, maps open/resolved/all correctly, and includes `available_actions` plus resolved evidence fields.
- [x] 4.2 Backend: `available_actions` includes `raise_budget` with the right cap key only for budget cap alarms and never includes `abort_session`/`adjust_guardrail`.
- [x] 4.3 Backend: `resolve_alarm` positive-cap guard applies a strictly-greater cap and rejects `<=` current with no budget change and alarm still open.
- [x] 4.4 Backend: canonical `/alarms` serves React on complete build and Jinja on missing/partial build; legacy open `/alarms` JSON route auth is unchanged.
- [x] 4.5 Backend: resolve returns JSON outcome for JSON callers (including sanitized rejection) and preserves the 303 redirect for HTML callers.
- [x] 4.6 Frontend source/contract test: view renders from `available_actions`, filter maps to `?filter=`, resolve uses `/alarms/{id}/resolve` with JSON Accept, no Abort/adjust_guardrail controls.
- [x] 4.7 `npm --prefix frontend run check`.

## 5. Verification

- [x] 5.1 `openspec validate react-alarms-inbox --strict`.
- [x] 5.2 `uv run pytest tests/portal/test_react_shell.py -q` and `uv run pytest -q`.
- [x] 5.3 `git diff --check`.
- [x] 5.4 Browser smoke: open `/alarms` with a complete build → React renders inside chrome; switch Open/Resolved/All (bookmarkable); Continue an alarm; Raise Budget on a budget alarm (preset + custom, confirm) and confirm authoritative refresh; attempt a non-increasing cap and confirm sanitized rejection; confirm missing-build fallback serves Jinja.
