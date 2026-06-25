## Context

The Portal is a server-rendered FastAPI/Jinja application with shared CSS in `base.html`, project/workflow templates under `src/agile_ai_htb/templates/`, and tests that assert rendered HTML. It already has the main product surfaces: project workspace, dashboard next actions, project-scoped board, Worker setup, sessions, alarms, and reports.

The quality gap is not a missing frontend framework. It is inconsistent visual primitives, dense setup/board surfaces, weak empty states, and raw governance evidence appearing before a concise explanation.

## Goals / Non-Goals

**Goals:**

- Make the existing Portal feel deliberate and easier to operate.
- Improve project workspace, board, setup, and evidence surfaces with small server-rendered changes.
- Standardize CSS classes for common cards, actions, alerts, empty states, toolbar/status rows, and evidence summaries.
- Use tiny vanilla JavaScript only for local feedback that directly improves current forms or refresh flows.
- Preserve existing routes, lifecycle states, launch guardrails, Review disposition, and project scoping.

**Non-Goals:**

- No React, Vite, SPA router, frontend build pipeline, or component framework.
- No drag/drop Kanban, websocket log streaming, modal-heavy redesign, or global command palette.
- No new database model unless existing route queries cannot provide required counts.
- No changes to Worker Adapter identity, tracking modes, model routing, or budget governance semantics.
- No automatic Done/Block/repair behavior; that remains outside this quality pass.

## Decisions

### Decision: Server-rendered polish first

Keep Jinja templates as the source of truth and improve shared CSS/utilities before adding frontend infrastructure.

Alternatives considered:

- React/Vite rewrite: rejected for this slice because the product pain is clarity and presentation, not complex client state.
- HTMX dependency: deferred; native links/forms plus small vanilla JS are enough until partial updates become painful.

### Decision: Shared CSS primitives instead of page-specific inline styles

Move repeated inline styling into small shared classes for page headers, action cards, toolbar rows, alert banners, empty states, evidence summaries, and compact metadata rows. Templates should read as product structure rather than CSS fragments.

Alternatives considered:

- Full design system: rejected as overkill.
- Leave inline styles: rejected because it keeps visual drift and makes quality work harder to review.

### Decision: Project workspace becomes the operator command center

`/projects/{project_id}` should summarize selected-repo state: readiness, task counts, running/review work, open alarms when available, and next useful actions. It should still link to existing pages rather than duplicating board/setup/session controls.

Alternatives considered:

- Keep it as link hub: rejected because it does not answer what the operator should do next.
- Project-scoped sessions/reports in this slice: deferred; link to existing global surfaces until real usage proves scoping is needed.

### Decision: Board quality focuses on status clarity, not workflow rewrite

The project board should show compact project/Worker/task status, column counts, clear empty states, and distinct launch error vs guardrail block vs human Blocked copy. Existing columns, forms, lifecycle states, and manual controls stay intact.

Alternatives considered:

- Drag/drop board: deferred until manual ordering is a real workflow need.
- Board SPA: rejected; current launch/review forms are server-friendly.

### Decision: Setup pages show one next missing action

Setup/readiness pages should guide the operator to the next missing step while keeping diagnostics and advanced details in native `<details>` blocks.

Alternatives considered:

- Wizard state machine: rejected because current routes already map to setup areas.
- Duplicate setup forms on dashboard/project pages: rejected; route attention to existing settings pages.

### Decision: Evidence summaries before raw evidence

Session/report/evidence surfaces should show a compact human summary first: launch target, Worker Adapter, Worker model, tracking mode, token split, alarms, review status, and result. Raw stdout/stderr/timeline payloads remain available behind `<details>`.

Alternatives considered:

- Hide raw evidence: rejected because governance needs auditability.
- Show raw evidence first: rejected because it makes the harness value harder to understand.

## Risks / Trade-offs

- CSS cleanup can become a drive-by redesign → Limit implementation to existing surfaces and remove inline duplication only where touched.
- Counts/actions can drift from board behavior → Derive from existing task/adapter/alarm/session data and cover with rendered-page tests.
- Better empty states can overpromise capability → Copy must point to existing actions only.
- Tiny JavaScript can accumulate into a hidden frontend app → Keep JS local to forms/refresh feedback; no client router or client-owned state.
- Evidence summaries can omit debugging detail → Keep raw details available via native disclosure.

## Migration Plan

1. Add shared CSS primitives and replace repeated inline styles only on touched pages.
2. Upgrade project workspace overview with existing data-derived status and next actions.
3. Upgrade project board toolbar, counts, empty/error/block states, preserving current forms.
4. Upgrade setup/readiness pages with next missing action and collapsed diagnostics.
5. Upgrade sessions/reports evidence summary display.
6. Add/adjust rendered HTML tests for the changed surfaces.
7. Run targeted portal tests, then `uv run pytest`.

Rollback: templates can fall back to the prior markup while preserving all existing backend behavior because this change does not require new lifecycle states or Worker execution semantics.

## Open Questions

- Should `project_workspace` show open alarms globally or only alarms tied to sessions/tasks in the selected project when that binding is available?
- Should session/report evidence summaries be added to the list page first or only to individual report pages first?
