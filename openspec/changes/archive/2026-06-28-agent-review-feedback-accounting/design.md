## Context

Agent Review already exists as Review-stage advisory work. The current route calls the configured control-plane/orchestrator model, creates a separate review session, and records a reporting token turn, but the board response is easy to miss and the token categorization/session evidence are not surfaced clearly enough.

## Goals / Non-Goals

**Goals:**

- Keep Agent Review in the control-plane model layer.
- Make Agent Review completion/failure visible on the Review task card after the existing redirect/refresh flow.
- Record Agent Review usage as orchestration/reporting spend that appears in budget summaries and session evidence.
- Preserve Worker execution actuals as Worker-only spend.
- Link the task's Agent Review result to its review session/model/token totals.

**Non-Goals:**

- Do not turn Agent Review into another Worker Adapter launch.
- Do not add a review-history table; latest task metadata plus the existing session/token ledger is enough.
- Do not change Review disposition semantics: Agent Review remains advisory and does not auto-Mark Done or Block.
- Do not redesign the board or sessions pages.

## Decisions

1. **Keep control-plane Agent Review.** Agent Review inspects completed Worker evidence; it is orchestration/reporting work. Reusing the Worker Adapter would create a second Worker Run and blur implementation execution with advisory review.

2. **Use existing token/session primitives.** Keep the separate Agent Review session and token turn, but classify the token turn under reporting/orchestration spend with `usage_source=control_plane`. This avoids a new table and keeps Worker `actual_tokens` clean.

3. **Store a small visible summary on task metadata.** Extend the existing `agent_review` metadata with review session id, model, status, recommendation, reviewed timestamp, and token totals. The board can render one concise line by default and keep findings/raw detail behind the existing Review details.

4. **Compute display totals from the token ledger.** The Agent Review response should use the persisted review session/token rows, not a separate counter, so `/sessions` and `/sessions/{id}` stay auditable.

## Risks / Trade-offs

- **Agent Review tokens inflate Worker actuals** → Mitigation: only Worker execution spend updates task `actual_tokens`; review tokens appear in orchestration/reporting budget summaries.
- **Board gets noisy** → Mitigation: render one concise status line by default; leave findings/details in existing expandable Review evidence.
- **Existing tests expect `reporting` usage kind** → Mitigation: preserve `usage_kind=reporting` while fixing spend category/source metadata and visible totals.
- **Review session missing token row on failure** → Mitigation: failed review still stores review session id/model/status/error; token totals may be zero and should display as such or omit the token count.
