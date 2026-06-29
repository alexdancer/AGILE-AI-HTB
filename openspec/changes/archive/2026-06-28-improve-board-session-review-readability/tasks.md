## 1. Board Card Width

- [x] 1.1 Increase the AGILE Board column/card minimum width in the existing shared CSS grid without changing board columns or actions.
- [x] 1.2 Update board rendering tests to assert the wider column minimum and preserved task controls.

## 2. Session Report Agent Review Results

- [x] 2.1 Add a small session-report view model that finds the task linked to the opened Worker session and exposes its latest `metadata.agent_review` when present.
- [x] 2.2 Render an Agent Review results section on the Worker session report with status, recommendation, summary, control-plane model, reviewed timestamp, review session link, token total, and bounded findings/failure details when available.
- [x] 2.3 Keep reports with no related Agent Review clean: do not show fabricated review results or zero review tokens.

## 3. Accounting and Verification

- [x] 3.1 Add or update portal session/report tests proving review results and review token totals appear on the reviewed Worker session report while Worker session token totals and task `actual_tokens` remain unchanged.
- [x] 3.2 Run `openspec validate improve-board-session-review-readability --strict` and targeted pytest for board/session/review surfaces.
- [x] 3.3 Run fresh `uv run pytest` before marking tasks complete.
