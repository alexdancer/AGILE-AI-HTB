## Why

The Portal has the right server-rendered workflow surfaces, but it still feels rough because the visual system, project overview, board guidance, setup guidance, and evidence summaries are inconsistent. Improving those surfaces now raises perceived product quality without buying a React/Vite frontend or changing the governance model.

## What Changes

- Add a lightweight Portal quality pass using the existing FastAPI/Jinja/CSS stack.
- Standardize shared layout, cards, buttons, alerts, empty states, and responsive table/board behavior.
- Upgrade the project workspace overview so it summarizes next actions for the selected repo instead of acting only as a link hub.
- Improve the project board with a compact status toolbar, useful empty states, clearer launch/error/blocking copy, and preserved manual controls.
- Improve setup/readiness guidance with one obvious next missing step and advanced diagnostics collapsed behind native details.
- Improve session/report evidence summaries so governance proof is readable before raw logs.
- Keep the current server-rendered architecture; no React, SPA router, frontend build pipeline, drag/drop board, or websocket requirement in this change.

## Capabilities

### New Capabilities
- `portal-quality-system`: Covers shared visual consistency, empty states, alert/action styles, responsive behavior, and minimal vanilla-JS feedback patterns for the Portal.
- `portal-evidence-readability`: Covers readable session/report evidence summaries for launches, models, token usage, alarms, review status, and raw evidence disclosure.

### Modified Capabilities
- `project-workspace`: The project workspace SHALL summarize actionable repo state and route the operator to the next useful workflow.
- `project-scoped-board`: The project board SHALL expose compact project/task/run/readiness status and clearer empty/error/blocking states without changing board lifecycle states.
- `guided-worker-setup`: Worker/setup pages SHALL present a single next missing setup action while keeping advanced diagnostics available but secondary.
- `dashboard-next-actions`: Dashboard and project/workflow next-action surfaces SHALL use consistent action-card styling and copy.

## Impact

- Portal routes and Jinja templates under `src/agile_ai_htb/routes/` and `src/agile_ai_htb/templates/`.
- Shared inline CSS in `base.html`; implementation may extract or consolidate classes but should not add a frontend build system.
- Existing portal tests for dashboard, projects, board, workers, sessions, alarms, and setup.
- No database schema requirement unless existing route data is insufficient for counts already available in current views.
