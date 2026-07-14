## 1. Backend: budget state JSON read

- [x] 1.1 Add an authenticated `/api/settings/budget` JSON endpoint in `src/foreman_ai_hq/routes/react_shell.py` guarded by `require_portal_auth`, deriving its response from `_effective_budget_settings(...)`.
- [x] 1.2 Return exactly: daily cap, per-session Worker cap, current-window used, current-window remaining, `budget_since`, last daily-usage reset timestamp; report absent cap/counter values as typed `null`, not fabricated zeros.

## 2. Backend: negotiated save/reset outcomes

- [x] 2.1 Extend `POST /settings/budget` in `portal.py` to return a sanitized JSON success envelope (saved authoritative state) when the caller negotiates `application/json`, preserving the existing HTML `303 → /setup` redirect for form callers.
- [x] 2.2 Return a sanitized JSON error envelope on invalid/non-positive caps for JSON callers with no raw exception/stack text; leave the persisted budget unchanged.
- [x] 2.3 Extend `POST /settings/budget/reset` to return a sanitized JSON outcome (refreshed counter state) for JSON callers, preserving the existing HTML redirect and all soft-reset evidence guarantees.
- [x] 2.4 Reuse the existing content-negotiation helper used by the alarm resolve / Restore outcomes rather than adding new negotiation logic.

## 3. Backend: build-aware canonical route

- [x] 3.1 Make `GET /settings/budget` serve the React shell when the complete build validates via the existing index-plus-referenced-assets helper, and render the existing Jinja `budget.html` at the same URL when the build is missing or partial.

## 4. Frontend: React Budget Settings view

- [x] 4.1 Add `frontend/src/views/BudgetSettings.jsx` inside the shell chrome: caps form, today's counter, spend-authority reference, soft-reset action.
- [x] 4.2 Wire the `/settings/budget` route in `frontend/src/App.jsx`; keep `Back to setup` as a full-page anchor.
- [x] 4.3 Load state from `/api/settings/budget`; submit save/reset with `Accept: application/json`; show inline success/sanitized error; refetch authoritative state after each without leaving the page or forcing `/setup`.
- [x] 4.4 Require an accessible confirmation dialog (correct focus handling) before submitting the reset.
- [x] 4.5 Ensure keyboard-operable controls, explicit labels, visible focus, semantic headings, and status/error announcements.

## 5. Tests

- [x] 5.1 In `tests/portal/test_react_shell.py`: `/api/settings/budget` requires portal auth and returns the exact bounded field contract.
- [x] 5.2 Negotiated outcomes: JSON save success/error envelopes (no leaked internals), JSON reset outcome, and unchanged HTML redirects for form callers.
- [x] 5.3 Build-aware `/settings/budget`: React when built, Jinja when missing/partial.
- [x] 5.4 React source/contract assertions for budget JSON field names and the save/reset action wiring.

## 6. Verify

- [x] 6.1 `openspec validate react-budget-settings-parity --strict`
- [x] 6.2 `npm --prefix frontend run check`
- [x] 6.3 `uv run pytest tests/portal/test_react_shell.py -q` then `uv run pytest -q`
- [x] 6.4 `git diff --check`
- [x] 6.5 Browser smoke: open built `/settings/budget`, save caps (stays on page, inline success), reset with confirmation, then load missing/partial build and confirm Jinja fallback at the same URL.
