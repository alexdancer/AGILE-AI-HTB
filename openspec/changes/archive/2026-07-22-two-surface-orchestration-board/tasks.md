## 1. Backend: state model and queries

- [x] 1.1 Add `list_task_breakdowns_for_project(database_path, project_id)` to `db.py` returning pending Proposed Task Breakdowns bound to the project, ordered newest first.
- [x] 1.2 Introduce Blocked Condition as task metadata (`blocked_condition`: reason, origin, timestamp); stop writing `status: "Blocked"`.
- [x] 1.3 DB migration: rewrite existing `status: "Blocked"` rows to `Estimated` plus a Blocked Condition (`manual estimate required` when no estimate, otherwise the recorded reason); assert no task retains a `Blocked` status.
- [x] 1.4 Change `board_automation.py` state from `active_task_id`/`active_worker_run_id` to an `active_runs` list; keep run-queue launch one-at-a-time.



## 2. Backend: routes and read-models

- [x] 2.1 Add the Execution Floor route at `/projects/{project_id}/floor` serving the React shell (missing/partial build → recovery response; unknown project → 404).
- [x] 2.2 Redirect `/projects/{project_id}/board` to `/projects/{project_id}`; keep the retired server-rendered board retired and rely on the existing missing-build recovery response.
- [x] 2.3 Add `/api/projects/{project_id}/needs-you` as a derived read-model aggregating pending breakdowns, manual-estimate conditions, guardrail-refused launches, Review tasks awaiting disposition, and pending budget overrides.
- [x] 2.4 Extend `/api/portal/nav` (or the board payload) with the Needs You count for the badge.



## 3. Frontend: routing and shell

- [x] 3.1 Add `pipeline` (project home) and `floor` views to `routes.js`/`App.jsx`; leave legacy project-board and `/app/projects/...` aliases server-owned so FastAPI can redirect them permanently.
- [x] 3.2 Update `Shell.jsx` nav: add the Execution Floor link under the active project and a Needs You count badge.



## 4. Frontend: Pipeline Surface

- [x] 4.1 Build the Pipeline Surface: project-identity/readiness header (absorbed from Workspace), task intake, Estimated tasks, and a Planning Inbox listing pending breakdowns that links to Task Breakdown Review.
- [x] 4.2 Pin the Needs You section at the top of the Pipeline Surface with a bounded empty state.
- [x] 4.3 Retire `Workspace.jsx`'s duplicate column preview; move its repo-binding and Restore action onto the Pipeline header.



## 5. Frontend: Execution Floor and Evidence Drawer

- [x] 5.1 Build the Execution Floor: one pane per active Worker Run, a review queue, and a recently-finished trail leading with estimate vs actual + Archive.
- [x] 5.2 Extract/confirm `EvidenceSection`/`BoundedText` are mountable outside the Session Report page; build the Evidence Drawer that fetches `/api/sessions/{id}/report` on open and mounts those shared components.
- [x] 5.3 Move Review Disposition actions (Agent Review, Mark Done, Block, review prompt) into the Evidence Drawer footer; keep the review queue visible beside it.
- [x] 5.4 Delete `TaskDetails` inline evidence from the board; render Blocked Condition as an in-place reason badge on cards.



## 6. Data and tests

- [x] 6.1 Update `demo_seed.py` to the Blocked Condition model (no `Blocked` status), seed a pending breakdown, and version/preflight every deterministic demo ID so unrelated task, session, run, alarm, breakdown, adapter, project, or repository data is never reused or overwritten.
- [x] 6.2 Update portal/e2e tests referencing the `Blocked` column and `/projects/{id}/board` to the new surfaces and routes; add tests for permanent server-owned aliases, missing-build recovery, Needs You aggregation, the breakdown list query, and fail-closed demo-ID collisions.
- [x] 6.3 Add frontend tests asserting the Evidence Drawer and Session Report render from shared components, the drawer fetches on open, and full evidence is absent from the board-card payload.



## 7. Docs and verification

- [x] 7.1 Update `CONTEXT.md` cross-references if any route names shifted during implementation; confirm ADR-0002/0003 remain accurate.
- [x] 7.2 Run `openspec validate two-surface-orchestration-board --strict`, `openspec validate --all --strict`, `uv run pytest`, the recorded-demo E2E, and `npm run check`; record fresh final-tree evidence before completion.