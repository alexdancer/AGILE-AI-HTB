## Why

The Orchestration Board is a single five-column kanban (`Board.jsx`) that tries to do four jobs at once — intake, queue control, the kanban, and full audit evidence inlined into every card — while `Workspace.jsx` renders a duplicate column preview and the planning half of the workflow (Proposed Task Breakdown review) is invisible once the user navigates away. `Running` is a column that only ever holds one card, card evidence duplicates `SessionReport` inside a `<details>` squeezed to a fifth of the viewport, and the persisted `Blocked` column mostly just means "has no estimate." This change reshapes the board so its structure stops misrepresenting the work, using capability already present — no estimation-engine or worker changes. It implements the decisions in `docs/adr/0002-two-surface-orchestration-board.md` and `docs/adr/0003-decision-queue-state-model.md` (slice A).

## What Changes

- Split the board into a **Pipeline Surface** at the project home `/projects/{id}` (intake, Planning Inbox of pending breakdowns, Estimated tasks) and an **Execution Floor** at `/projects/{id}/floor` (running panes, review queue, recently-finished trail).
- **BREAKING**: `/projects/{id}/board` redirects to the Pipeline Surface. The retired server-rendered board is not reintroduced; missing React builds use the existing recovery response.
- Retire the `Workspace.jsx` column-preview duplicate; the project home is the Pipeline Surface.
- Move card audit evidence into an **Evidence Drawer** that reuses `SessionReport`'s exported `EvidenceSection`/`BoundedText` from one implementation; delete `TaskDetails` from the board. Review actions (Mark Done / Block) live in the drawer.
- Add a project-scoped **Needs You** queue pinned atop the Pipeline Surface with a live count badge in project navigation, aggregating pending breakdowns awaiting review, tasks needing a manual estimate, guardrail-refused launches, runs awaiting review disposition, and budget overrides.
- Replace the persisted `Blocked` column with a **Blocked Condition** flag that preserves the task's lifecycle state and position and shows a reason badge.
- Add the missing `list_task_breakdowns_for_project` query so pending Proposed Task Breakdowns stop orphaning after intake navigates away.
- Surface **estimate vs actual** on the Floor's recently-finished trail rather than in a `task-meta` span.
- `board_automation` state moves from a singular `active_task_id` to a list so the Floor can project every active project run while queue automation remains bounded and one-at-a-time.

## Capabilities

### New Capabilities
- `execution-floor`: the execution half of the board — one pane per active Worker Run, a review queue whose cards open the Evidence Drawer, and a recently-finished trail leading with estimate vs actual.
- `needs-you-queue`: project-scoped aggregation of everything awaiting a human decision, pinned atop the Pipeline Surface with a navigation count badge; distinct from Alarms.

### Modified Capabilities
- `react-board-workflow`: the board renders as Pipeline + Floor; the `Blocked` column is replaced by the Blocked Condition flag.
- `board-launch-selection`: workflow blockers remain in canonical lifecycle positions with structured Blocked Conditions rather than a `Blocked` column.
- `project-scoped-board`: `/projects/{id}` becomes the Pipeline Surface and `/projects/{id}/board` redirects to it.
- `project-board-run-automation`: automation controls move to the Floor, expose every active run, and write collection-based active-run state while reading legacy singular state.
- `project-archive-visibility`: archived Pipeline/Floor access remains restore-first with retained session and task-history evidence.
- `project-workspace`: the column-preview duplicate is retired; the project home is the Pipeline Surface.
- `react-portal-shell`: canonical React route ownership and exact workspace links/counts expand to Pipeline + Floor while legacy board aliases redirect to Pipeline.
- `task-review-disposition`: Mark Done / Block actions move into the Evidence Drawer alongside the evidence they act on.
- `governed-worker-launch`: safety and launch blockers become structured Blocked Conditions while tasks retain canonical lifecycle status; successful retries clear resolved blockers.
- `task-breakdown-review`: failed Acceptance Verification remains in Review with a Blocked Condition rather than entering a `Blocked` lifecycle status.
- `portal-evidence-readability`: inline card `TaskDetails` is replaced by the Evidence Drawer reusing shared `SessionReport` evidence components.
- `markdown-task-intake`: pending Proposed Task Breakdowns are listed in the Pipeline Surface Planning Inbox via the new `list_task_breakdowns_for_project` query.

## Impact

- Frontend: `Board.jsx` (Pipeline/Floor modes plus Evidence Drawer and Needs You), `Workspace.jsx` route retired, `Shell.jsx` nav (Floor link + Needs You badge), `App.jsx`/`routes.js` route table, `SessionReport.jsx` (export/reuse evidence components).
- Backend: `board_automation.py` (`active_task_id` → list), `db.py` (`list_task_breakdowns_for_project`; Blocked Condition metadata replacing `status: "Blocked"`), `routes/` (Floor route, `/board` redirect, existing missing-build recovery, Needs You endpoint).
- Data/tests: demo seed and portal/e2e tests that encode the `Blocked` column and the `/projects/{id}/board` route.
- Non-goals: no change to `estimation.py` (integer estimator stays); no estimation provenance display; no Scout task kind; no worktree isolation; no parallel queue policy.
