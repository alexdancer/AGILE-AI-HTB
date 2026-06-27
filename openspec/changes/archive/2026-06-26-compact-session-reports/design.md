## Context

The Portal is FastAPI/Jinja with shared inline CSS in `base.html`. Existing session pages already summarize evidence before raw sections, but several fields still render unbounded text: session task descriptions on `/sessions`, task/report text in the session report header, evidence summary values, and timeline detail summaries. Raw repo context is already behind a disclosure section with a bounded `<pre>`, so the problem is mostly default text density, not data modeling.

## Goals / Non-Goals

**Goals:**

- Make `/sessions` scan-friendly by showing compact task/session summaries by default.
- Make `/sessions/{session_id}` readable above the fold by bounding task text, launch target, project labels, result text, and timeline detail summaries.
- Preserve full evidence for audit through native `<details>` sections or bounded scroll regions.
- Reuse small shared CSS utilities and server-rendered templates.

**Non-Goals:**

- No database schema changes.
- No deletion, truncation, or mutation of persisted evidence.
- No React/Vite/SPA, custom accordion JavaScript, websocket logs, or new frontend dependency.
- No change to Worker Adapter execution, tracking mode, token accounting, model selection, or budget governance.

## Decisions

1. **Use shared CSS utilities, not new route state, for most compaction.**
   - Add small reusable classes such as compact line clamps, wrap-anywhere text, and bounded raw blocks.
   - Rationale: the text already exists in template context and can be made readable without schema or backend formatting.
   - Alternative rejected: persist summary fields in the database; that creates stale derived data for a display-only concern.

2. **Keep raw evidence visible on demand with native HTML.**
   - Full task descriptions, command/launch targets, repo context text, and long timeline details remain in `<details>` or bounded scroll blocks.
   - Rationale: governance needs auditability; hiding by default is acceptable, removing is not.
   - Alternative rejected: hard truncate strings server-side; that risks losing evidence in rendered reports.

3. **Apply only to session evidence surfaces in this slice.**
   - Touch `/sessions` and `/sessions/{session_id}` plus shared CSS used by those templates.
   - Rationale: board card readability already has related patterns; this change should stay scoped to session reports unless implementation exposes an obvious shared utility reuse.
   - Alternative rejected: broad Portal rewrite; the current pain is dense text, not client-state complexity.

## Risks / Trade-offs

- **Risk: CSS-only clamping may hide important failure text.** → Keep concise failure/result fields visible and expose full text immediately below in a disclosure section when it is long.
- **Risk: Operators may think raw evidence was removed.** → Label disclosures clearly as full task text, raw repo context, timeline details, or raw evidence.
- **Risk: Browser support for line clamp varies.** → Use graceful fallback with wrapping/overflow bounds; readability improves even if clamping is ignored.
- **Risk: Over-compaction makes audits slower.** → Keep evidence counts, status, model, token totals, and review state visible in the default summary.
