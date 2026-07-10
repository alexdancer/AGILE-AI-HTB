## Why

React `/app/projects/{id}/board` currently displays a read-only project board with only basic queue controls, then sends operators to Jinja for intake, per-card launch, refresh, review, archive, diagnostics, and evidence. This preserves safety but leaves the React surface split-brain after dashboard parity.

The next migration phase must let an operator complete the normal, project-scoped board loop in React without duplicating FastAPI lifecycle, budget, Worker Run, or review authority.

## What Changes

- Replace the React board's read-only/Jinja-handoff behavior with the normal project-board workflow: intake → estimate or Task Breakdown Review → launch → running refresh → review → Done/Blocked → archive or dismiss.
- Keep existing FastAPI POST action paths authoritative. Add JSON-capable outcomes to existing project-scoped intake, run-next, queue, archive, and task-action flows where a React caller needs a non-redirect response; do not introduce a parallel generic mutation API or new persistence model.
- Replace the raw React board-context response with an explicit bounded card projection. Include only fields needed for cards, controls, details, and links; redact and bound evidence before returning it.
- Preserve the five canonical columns, project scope, existing launch guardrails, Worker Adapter allowed-model constraints, budget/native-usage acknowledgements, queue stop conditions, and human Review Disposition.
- Render compact React cards with native details for full task text, token components, launch metadata, bounded timeline/log evidence, review findings, and blocked details. Launch evidence uses actual Worker model first; routed recommendation remains secondary when different.
- Keep the Jinja board available as fallback during this phase. React remains non-default until the separate default-enable gate.

## Capabilities

### New Capabilities
- `react-board-workflow`: React project-board presentation, bounded state projection, existing-action JSON outcomes, workflow controls, and evidence disclosure contract.

### Modified Capabilities
- `react-portal-shell`: React project boards become full workflow-capable rather than a read-only shell linking to Jinja for normal board actions.
- `board-filtering`: Preserve zero-dependency local filtering for both server-rendered and React-owned board surfaces without server requests per keystroke.

## Impact

- Frontend: `frontend/src/views/Board.jsx`, new focused board components/helpers/tests, shared CSS tokens.
- Backend: `src/agile_ai_htb/routes/react_shell.py`, existing task and project-board action routes, board view-model/projection helpers, and portal tests.
- Existing backend workflow rules remain authoritative: task intake/breakdown, estimation, model routing, launch guardrails, Worker Run lifecycle, queue automation, review disposition, task archive visibility, and token accounting.
- No schema migration, new Worker Adapter mode, control-plane model change, dependency, WebSocket, drag/drop board rewrite, or React default-landing change.
