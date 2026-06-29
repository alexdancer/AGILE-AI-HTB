## Context

The Portal already uses server-rendered FastAPI/Jinja pages, shared CSS in `base.html`, task metadata for Agent Review results, and token ledger rows for review sessions. The current gap is presentation: board cards are cramped, and the Worker session report does not surface the Agent Review result that belongs to the task linked to that session.

## Goals / Non-Goals

**Goals:**

- Make AGILE Board task cards wider with the existing CSS grid/column layout.
- Surface related Agent Review results on the reviewed Worker session report.
- Show Agent Review token totals, review model, recommendation, findings, and review session link where available.
- Preserve accounting semantics: review tokens are reporting/orchestration spend and do not change Worker `actual_tokens`.
- Keep the implementation small and covered by focused portal tests.

**Non-Goals:**

- No new board workflow, columns, drag/drop, SPA, websocket stream, or component framework.
- No database schema or review-history table.
- No change to Worker Adapter launch behavior or model-layer ownership.
- No attempt to merge Agent Review token totals into Worker execution actuals.

## Decisions

- Widen cards by increasing the existing `.columns` `minmax(...)` width in shared CSS.
  - Rationale: one CSS value fixes the cramped cards without touching board behavior.
  - Alternative rejected: redesigning card layout or replacing the board grid.

- Pass a small related-review view model into `session_report.html` for Worker sessions.
  - Rationale: the needed review result already lives on the task metadata; the report only needs to look up the task whose `session_id` matches the report.
  - Alternative rejected: adding a review table before review history is a requirement.

- Render review results as a compact section before raw evidence, with findings and full details bounded/expandable.
  - Rationale: matches existing summary-first evidence surfaces and preserves auditability.
  - Alternative rejected: dumping raw task metadata into the report.

- Keep review token totals sourced from `task.metadata.agent_review.token_totals` and linked `review_session_id`.
  - Rationale: this preserves the control-plane/orchestration accounting split and lets operators open the separate review session report for raw review usage.
  - Alternative rejected: adding review tokens to task `actual_tokens` or Worker session totals.

## Risks / Trade-offs

- Related task lookup by session id is a simple scan of existing tasks → acceptable for the current local/operator portal; add an indexed DB helper only if task volume proves it necessary.
- A task can have missing or failed review token metadata → render status/model/session link when present and label missing token totals without fabricating zero.
- Wider cards increase horizontal scroll on small screens → existing board already scrolls horizontally; mobile can keep the existing responsive behavior.
