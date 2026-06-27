## 1. Shared Readability Utilities

- [x] 1.1 Add small shared CSS utilities in `base.html` for compact line clamps, wrap-anywhere text, and bounded raw evidence blocks.
- [x] 1.2 Reuse existing task/card readability styles where possible instead of adding one-off inline styles.

## 2. Sessions Index

- [x] 2.1 Update `sessions.html` so each row shows a compact task/session summary by default.
- [x] 2.2 Preserve visible scan fields on each row: session link, model, status, prompt/completion/total tokens, evidence counts, zone, and alarms.
- [x] 2.3 Ensure full task text remains reachable from the session report rather than being lost or mutated.

## 3. Session Report

- [x] 3.1 Update `session_report.html` header and evidence summary cards to use bounded/wrapping previews for task text, project labels, launch targets, status/result text, and missing-evidence labels.
- [x] 3.2 Move or keep full task text and long raw evidence behind native `<details>` or bounded raw evidence sections.
- [x] 3.3 Bound expanded raw sections such as repo context brief text and long timeline details so opening them does not make the page unusable while scrolling.
- [x] 3.4 Keep concise failure/result evidence visible before raw stderr, stdout, command payloads, or diagnostic details.

## 4. Tests and Verification

- [x] 4.1 Add or update rendered-page tests proving `/sessions` does not render an unbounded long task as the default table cell while preserving key scan fields.
- [x] 4.2 Add or update session report tests proving compact summaries render and full evidence remains available behind disclosure/bounded raw sections.
- [x] 4.3 Run targeted Portal/session tests.
- [x] 4.4 Run `openspec validate compact-session-reports --strict`.
- [x] 4.5 Run `uv run pytest`.
