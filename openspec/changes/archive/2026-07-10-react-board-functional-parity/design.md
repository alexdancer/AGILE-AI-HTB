## Context

The React shell already owns `/app`, `/app/projects/{id}`, and `/app/projects/{id}/board`, but the board is intentionally incomplete. It reads `board_page_context()` through `/api/projects/{id}/board`, displays columns and basic automation controls, and links operators to Jinja for task intake, launch, refresh, review, archive, diagnostics, and full evidence.

The Jinja board already implements the authoritative project-scoped workflow. FastAPI owns authentication, task breakdown and estimation, adapter-aware model routing, launch guardrails, Worker Runs, budget acknowledgements, queue automation, review disposition, archive visibility, and evidence persistence. The React board must become a presentation layer over those rules, not a second workflow engine.

The current React board endpoint spreads raw `board_page_context()` into JSON. That includes complete task metadata and adapter view models, which is wider than a browser board needs and is not an acceptable evidence boundary for a migrated operator surface.

## Goals / Non-Goals

**Goals:**

- Complete the normal project-scoped board loop in React: intake, estimation or Task Breakdown handoff, launch, running refresh, review, disposition, archive/dismiss, and board automation controls.
- Keep FastAPI routes and lifecycle validation authoritative.
- Return explicit bounded board/card projections with sanitized evidence.
- Preserve compact-card-first readability with native details and existing Jinja fallback.
- Preserve project binding, Worker Adapter allowed-model selection, tracking-mode labels, budget/native-usage acknowledgement, queue policy, Worker-only task actuals, and human Review Disposition.

**Non-Goals:**

- No schema/data migration, new generic REST mutation API, frontend-owned lifecycle state, or duplicated guardrail/budget/model-routing rules.
- No Worker Adapter, tracking-mode, control-plane model, token-accounting, or queue-policy semantic change.
- No WebSockets, polling stream, drag/drop, state-management dependency, custom accordion system, or React default-landing change.
- No migration of the Jinja Task Breakdown Review, session/report, setup, or task-history pages into React.

## Decisions

### Use existing action paths with negotiated JSON outcomes

React will call the established project/task POST action paths, sending JSON or multipart payloads with `Accept: application/json`. Action routes will keep browser/form redirect behavior for callers that do not negotiate JSON and return `application/json` outcomes with fixed `ok`, `error`, `setup_href`, and `next_href` fields for React callers. Project-scoped intake will return either an updated task/board outcome or an explicit `next_href` for the existing Task Breakdown Review page.

This keeps validation, project binding, lifecycle transitions, error semantics, and side effects in their existing handlers. It avoids a parallel generic mutation API while preventing a React form submit from leaving the migrated board unexpectedly.

**Alternative:** Create new `/api/...` mutation wrappers for every board action. Rejected: duplicates route ownership and makes backend behavior drift more likely.

**Alternative:** Use ordinary form submissions from React. Rejected: redirects users into the Jinja board and fails functional parity.

### Replace raw board context with an explicit projection

`board_page_context()` remains the source of task grouping, adapter readiness, summaries, and automation state. The React handoff converts it into an allowlisted payload:

- project identity and board summary/history link;
- canonical columns and local-filter fields;
- per-card summary, lifecycle/status-specific action flags, allowed adapter/model selection data, estimate/recommendation/run/actual-token fields, and relevant workflow links;
- automation queue summary and live-refresh state;
- details fields only for task text, Worker token components, sanitized launch evidence, newest six timeline events, sanitized/bounded logs, Agent Review result, and blocked/manual-estimate evidence.

The projection must not return raw task metadata, adapter config/verification payloads, session keys, command secrets, raw token ledger entries, or unbounded evidence. Evidence uses the existing secret redaction/sanitization path and bounded strings before serialization.

The stable projection contract uses top-level `project`, canonical-status `columns`/counts/empty states/`tasks_by_status`, `board_summary`, `history_href`, `automation`, and `adapters` only. Every card uses fixed `summary`, token/model, named action booleans in `controls`, and fixed `details` sections. Each potentially long text value—including launch errors/diagnostics and timeline detail—is represented as `{text, truncated}`; unavailable scalar values are `null`, and unavailable collections are empty. Details preserve summary text (400-character maximum), task body (12,000), launch/log/review/blocked strings (4,000), newest six timeline entries with 1,000-character summaries, and at most 20 Agent Review findings with 1,000-character messages. Redaction occurs before truncation. The implementation tests every nested key and each null/empty/truncation rule, including Review status, recommendation/failure, model, token total, and review-session link.

**Alternative:** Keep spreading `board_page_context()` into JSON. Rejected: it leaks unnecessary internal state and makes frontend contracts unstable.

**Alternative:** Fetch each card's detail evidence lazily from a new endpoint. Rejected for this phase: increases route surface and interaction complexity without evidence that the bounded project board payload is too large.

### React state refreshes from backend after every mutation

Board mutation success or handled failure updates React from authoritative responses, then refetches the bounded board state. Running/queue state uses the existing project board-status endpoint on its current short interval only while active work or queue automation exists. Manual refresh remains visible for Running cards.

React will not locally infer status transitions, token totals, launch readiness, queue eligibility, or review availability.

**Alternative:** Optimistically move cards between columns in client state. Rejected: launch guardrails and asynchronous Worker Runs can invalidate the prediction.

### Preserve normal workflow actions and model-layer boundaries

Estimated cards retain adapter and allowed-model selectors, budget override and native-usage acknowledgement controls, then call the existing launch flow. Running cards retain manual refresh. Review cards retain saved prompt, Agent Review, Mark Done, and Block actions. Agent Review remains a control-plane/orchestrator-model operation; it is advisory and never becomes Worker Adapter usage or task actual Worker tokens. Done/Blocked archive and Estimated dismiss keep existing archive-visibility semantics and route to the existing task-history page.

### Use compact cards with native details

Default React cards show a clamped summary, estimate, normalized Worker actual where present, actual launch model when present, secondary routed recommendation when different, and status-specific primary controls. Native details disclose bounded task/evidence sections. A React-local filter operates on loaded card text/metadata with no request per keystroke.

### Keep Jinja fallback and default routing unchanged

Jinja board, Task Breakdown Review, history, session/report, setup, and error fallback routes remain reachable. Root, login, logout, and explicit React route ownership do not change. React remains non-default until the later default-enable change verifies dashboard and board parity.

## Risks / Trade-offs

- **Existing form parsing treats multipart as HTML-oriented** → Make response representation depend on explicit `Accept` negotiation, while preserving Jinja redirect tests.
- **Raw metadata/config leaks through board JSON** → Use dedicated allowlists with nested-key tests and redaction/boundary tests.
- **Client/server card state drifts after actions** → Refetch authoritative board state after every mutation; do not optimistic-transition cards.
- **Large evidence payload harms board responsiveness** → Limit timeline to the existing newest-six view, sanitize/bound detail strings, keep raw session reports linked separately.
- **Task Breakdown Review is not React-migrated** → Return an explicit review URL and navigate to its authoritative Jinja route rather than creating a partial React review flow.
- **Queue or Worker Run transition is missed** → Reuse existing board-status polling only while it reports active work/queue; keep manual refresh.
- **React appears default-ready too early** → Retain explicit experimental route, Jinja fallback links, and default-landing contract.

## Migration Plan

1. Add the bounded React projection and negotiated action outcomes behind the existing authenticated routes.
2. Replace the React Board view with focused controls/components using those contracts and backend refetch.
3. Add backend auth, projection, negotiation, project-scope, guardrail/error, and redaction tests; add frontend render/action/filter contracts.
4. Build frontend and run targeted/full verification before promoting any route behavior.

No persisted data migration is required. Rollback restores the prior read-only React Board view and JSON handoff; Jinja board workflows and task data remain unaffected.

## Open Questions

None. Route ownership, backend authority, evidence boundary, and Jinja fallback were agreed during exploration.
