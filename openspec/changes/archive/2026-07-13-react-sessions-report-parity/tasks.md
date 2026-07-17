## 1. Backend Contracts and Regression Tests

- [x] 1.1 Add failing Portal tests for canonical `/sessions` and `/sessions/{session_id}` route selection: complete build serves React, missing/partial build preserves Jinja, auth remains required, and unknown session ids remain `404`.
- [x] 1.2 Add failing endpoint tests for Sessions list auth, `started_at DESC, id DESC` pagination, exact nested keys/types, fixed bounds/defaults, `422` query validation, active-only poll metadata, generated links, redaction, and forbidden-field exclusion.
- [x] 1.3 Add failing endpoint tests for Session Report auth, exact top-level/nested keys and types/nullability, non-null and nullable integer/cost malformed defaults, token/category/component parity, related Agent Review separation, generated links, redaction, and forbidden-field exclusion.
- [x] 1.4 Add failing endpoint tests for every fixed/dynamic evidence collection, stable tie-break ordering, nested Repo source and Agent Review finding pagination, per-section limits/query validation, unknown-id rejection, missing sessions, and access beyond every initial page.
- [x] 1.5 Add failing continuation tests proving every truncated task/summary/raw/detail/repo/checkpoint/review preview emits an authenticated generated `full_href` returning complete redacted no-store text, while unknown selectors and arbitrary paths return `404`.
- [x] 1.6 Add failing freshness tests proving exact field types/bounds, 64-character SHA-256 version stability/change sources, explicit append/status boundary, terminal state, internally consistent embedded report version, and absence of report evidence/secrets.

## 2. Shared Session State and Bounded Handoffs

- [x] 2.1 Extract shared Sessions index and Session Report context builders from the current Jinja handlers without changing Jinja behavior or token/review calculations.
- [x] 2.2 Implement reusable sanitize/redact-before-preview primitives, exact scalar/cost/malformed defaults, bounded-text objects, generated collection/full-text URL allowlists, and exact projection helpers for Sessions/report fields.
- [x] 2.3 Implement bounded newest-first `/api/sessions` pagination and active-only poll metadata using the shared index state.
- [x] 2.4 Implement `/api/sessions/{session_id}/report` with summary, token totals/categories/components, initial paged evidence collections, related Agent Review, freshness, and fixed links.
- [x] 2.5 Implement allowlisted `/api/sessions/{session_id}/evidence/{collection_id}` pagination for top-level collections, nested Repo documents/manifests, and Agent Review findings with exact stable ordering and query limits.
- [x] 2.6 Implement generated `/api/sessions/{session_id}/text/{text_id}` continuations that recompute only allowlisted report evidence, fully redact it, return no-store text, and reject arbitrary selectors.
- [x] 2.7 Implement the append/status revision helper and `/api/sessions/{session_id}/freshness` with exact SHA-256 representation and one-read-snapshot parity without serializing full raw report evidence.

## 3. Canonical Route Migration

- [x] 3.1 Make the authenticated canonical Sessions list/report GETs return the React index only when the complete existing build validator passes, while executing the unchanged Jinja builders for missing/partial builds.
- [x] 3.2 Preserve backend `404` validation before serving the report shell and verify no `/app/sessions` route is introduced.

## 4. React Sessions List

- [x] 4.1 Add frontend route/parser and FastAPI shell-serving tests for canonical `/sessions` and `/sessions/:sessionId`, plus active Sessions sidebar state and in-shell canonical links.
- [x] 4.2 Implement the React Sessions view with semantic compact rows, exact scan fields, loading/empty/error states, bounded pagination, preserved last-good state, and practical keyboard/focus behavior.
- [x] 4.3 Implement five-second Sessions polling only while `has_active` is true, with cleanup on unmount, quiet unchanged refreshes, sanitized retry state, and `aria-live` status behavior.

## 5. React Session Report

- [x] 5.1 Add frontend tests covering Worker and Agent Review summaries, token categories/components/raw usage, every top-level/nested paged collection, missing evidence, related review separation, truncation notices, authenticated full-text actions, and Load-more behavior.
- [x] 5.2 Implement compact-first Session Report sections for identity/launch/review summary and normalized versus provider/control-plane token evidence using existing shell/design-system patterns.
- [x] 5.3 Implement semantic disclosures, paged Load-more controls for all top-level/nested collections, and explicit full-text loading for truncated evidence without exposing arbitrary JSON or selectors.
- [x] 5.4 Implement active-report freshness polling: detect opaque version changes, show `New session evidence available`, replace report only after explicit successful Refresh, preserve evidence on failure, and stop on terminal/unmount.
- [x] 5.5 Add/adjust shared frontend styles only as needed for bounded raw evidence, semantic tables, visible focus, non-color-only state, live notices, and desktop readability.

## 6. Verification and Review

- [x] 6.1 Run focused backend and frontend tests, `npm --prefix frontend run check`, and built/missing/partial route smoke checks; fix all regressions.
- [x] 6.2 Run browser smoke through Sessions list → Session Report → nested pagination/full text → Back; exercise keyboard pagination/disclosures, visible focus, live-region announcements, unchanged-poll focus/disclosure preservation, active-list polling, explicit report refresh, and Jinja fallback with the build unavailable.
- [x] 6.3 Run `uv run pytest -q`, `openspec validate react-sessions-report-parity --strict`, `openspec validate --specs --strict`, and `git diff --check`.
- [x] 6.4 Perform independent review for contract fidelity, bounded/redacted projections, Jinja parity/fallback, polling lifecycle, accessibility, security/privacy, regression risk, and maintainability; resolve every blocking or significant finding and rerun affected checks.
