## Why

The AGILE Board cards are too narrow for the current review/launch metadata, and session reports do not make completed Agent Review results and review token spend obvious when an operator opens the related Worker session report. This makes the review flow feel incomplete even though the evidence is already mostly captured.

## What Changes

- Make AGILE Board task cards wider by increasing the existing board column/card minimum width without changing the board workflow.
- Show completed Agent Review results on the relevant session report when a task linked to that session has review metadata.
- Show Agent Review token totals, model, recommendation, findings, and review session link in the session report.
- Preserve the existing split where Agent Review uses the control-plane/orchestrator model and counts as reporting/orchestration spend, not Worker execution `actual_tokens`.
- Keep the implementation server-rendered and minimal: template/CSS plus route view-model wiring and focused tests.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `board-card-readability`: Board cards should have a wider default card/column footprint while retaining compact default content and native details.
- `portal-evidence-readability`: Session reports should surface related Agent Review results and review token totals before raw evidence.
- `task-review-disposition`: Agent Review evidence should remain visibly connected to both the review task card and the session report for the reviewed Worker session.

## Impact

- Affected code: `src/agile_ai_htb/templates/base.html`, `src/agile_ai_htb/templates/session_report.html`, `src/agile_ai_htb/routes/portal.py`.
- Affected tests: portal board/session report tests and review action tests as needed.
- No database schema change, new dependency, SPA rewrite, or Worker Adapter behavior change.
