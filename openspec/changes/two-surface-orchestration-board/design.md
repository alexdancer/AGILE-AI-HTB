## Context

The board today is `Board.jsx` (five columns + intake + queue control + inline `TaskDetails` evidence) with a duplicate column preview in `Workspace.jsx`. Routing is a `parseRoute`/`App.jsx` table; nav is `Shell.jsx` drawing from `/api/portal/nav`. Backend board state comes from `/api/projects/{id}/board`; `board_automation.py` holds a singular `active_task_id`; task status is a string column in `db.py` with `"Blocked"` as one value; Proposed Task Breakdowns have get-by-id but no list-by-project. `SessionReport.jsx` already exports `EvidenceSection` and `BoundedText`. This slice reshapes those surfaces without changing the estimation algorithm or Worker Adapter execution contract. Motivation and alternatives are in `docs/adr/0002` and `docs/adr/0003`.

## Goals / Non-Goals

**Goals:**
- Two surfaces: Pipeline (`/projects/{id}`) and Floor (`/projects/{id}/floor`), from the existing board payload.
- One evidence implementation shared by the Floor drawer and the Session Report.
- Blocked Condition as a non-relocating flag; Needs You as a project-scoped decision queue.
- Fix breakdown orphaning with `list_task_breakdowns_for_project`.
- Keep the change reversible and backend-authoritative.

**Non-Goals:**
- No `estimation.py` change, no estimation provenance display, no Scout kind (later slices).
- No worktree isolation or parallel queue policy; queue automation remains one-at-a-time while the Floor projects every independently active project run.
- No new task lifecycle states; no hard-delete of history.

## Decisions

- **Blocked Condition is metadata, not a status value.** Add a `blocked_condition` object (reason, origin, timestamp) to task metadata; the task keeps its real lifecycle status (`Estimated`/`Review`). Migrate existing `status: "Blocked"` rows: those with an estimate → `Estimated` + condition; those without → `Estimated` + `manual estimate required` condition. *Alternative — keep the status and add a flag:* rejected, it keeps the dead column semantics the ADR retires.
- **Evidence Drawer fetches on open.** The drawer calls `/api/sessions/{id}/report` when opened rather than inflating the Floor payload (today's board already ships a bounded timeline per Running card). It mounts the exported `SessionReport` components directly. *Alternative — inline evidence in the board payload:* rejected for payload weight and to keep one fetch path.
- **`board_automation` state becomes a list now.** Change `active_task_id`/`active_worker_run_id` to `active_runs: []` so persisted state and the Floor can represent multiple independently active runs. Run-queue logic still launches one queue task at a time, and legacy singular state remains readable.
- **Needs You is a derived read-model over one endpoint.** Add `/api/projects/{id}/needs-you` that aggregates from existing tables (breakdowns awaiting review, tasks with `manual estimate required` conditions, guardrail-refused launches, `Review` tasks awaiting disposition, pending budget overrides). No new persistence; it is a projection. The nav badge count comes from the same endpoint via `/api/portal/nav` or a lightweight count field.
- **Pipeline absorbs project-status, so retiring Workspace loses nothing.** The few non-duplicated bits of `Workspace.jsx` (repo binding, restore action) move onto the Pipeline Surface header; only the redundant column preview is deleted.
- **Route handling.** `/projects/{id}/board` returns a redirect to `/projects/{id}`. The retired Jinja board stays retired; missing or partial React builds use the existing recovery response at the canonical route. `parseRoute` gains `pipeline` (project home) and `floor` views.

## Risks / Trade-offs

- **Migration of live `status: "Blocked"` tasks** → one-time DB migration with a test asserting no task remains in a `Blocked` status and each carries a condition; demo seed updated in the same change.
- **Two surfaces = two polling loops** (Pipeline live-refresh + Floor live events) → reuse the existing `live_refresh_enabled` gating so polling only runs while active work exists; the Floor owns the event feed, the Pipeline does not.
- **Shared evidence components must stay decoupled from `SessionReport` page chrome** → the reuse boundary is the already-exported `EvidenceSection`/`BoundedText`; if they still assume page context, extract them cleanly before mounting in the drawer.
- **Deep links / tests reference `/projects/{id}/board`** → the redirect preserves them; portal/e2e tests updated to the new routes in this change.

## Migration Plan

1. DB migration: rewrite `status: "Blocked"` rows to `Estimated` + `blocked_condition`; add `list_task_breakdowns_for_project`.
2. Backend: `active_runs` list, Needs You endpoint, `/board` redirect, and existing missing-build recovery.
3. Frontend: Pipeline + Floor views, Evidence Drawer, Needs You section + nav badge, route table, retire Workspace preview.
4. Update demo seed + portal/e2e tests. Rollback is reverting the change; the migration is forward-compatible (conditions are additive metadata).

## Resolved Questions

- The Needs You badge count is projected through the existing `/api/portal/nav` payload and refreshed from authoritative board loads/actions.
