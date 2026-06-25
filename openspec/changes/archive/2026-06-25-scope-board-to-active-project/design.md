## Context

Project workspace entry made `/projects` and `/projects/{project_id}` the operator's repo entry point, while the task board, task intake, task breakdown acceptance, sessions, and Worker launch still operate on global data. The current board route has no project parameter, and normal launch root resolution can fall back to the most recently updated connected project. That is unsafe once the UI implies the operator is working inside a selected repository.

The existing data model already stores project identity in `connected_projects` and task metadata already carries project binding for read-only proof/write-capable paths. This change should extend that metadata binding to normal board-created tasks before considering a table migration.

## Goals / Non-Goals

**Goals:**
- Make `/projects/{project_id}/board` the normal task board for a selected project workspace.
- Ensure project board task creation, estimate form intake, markdown upload/paste task breakdowns, accepted breakdown candidates, launch, refresh/review redirects, and task cards preserve selected project context.
- Ensure Worker launch uses the task's bound project root and rejects mismatched or missing project binding before process creation.
- Keep `/board` safe by redirecting to a concrete project board or project selection instead of silently acting as a global launch surface.
- Preserve OpenCode explicit directory binding and existing Worker Adapter/tracking-mode semantics.

**Non-Goals:**
- No project-scoped sessions/reports/dashboard migration in this slice.
- No dedicated `project_id` column migration unless implementation proves metadata is insufficient.
- No Worker Adapter identity, allowed-model, model-provider, tracking-mode, or budget-accounting redesign.
- No SPA board rewrite, drag/drop board, websocket updates, or new launcher abstraction.

## Decisions

1. **Use project-scoped board route as the source of selected project context.**
   - `/projects/{project_id}/board` resolves the connected project and passes `active_project` to the board template.
   - The project overview links to this route.
   - `/board` redirects to the most-recent connected project board when possible, otherwise `/projects`.
   - Alternative: store selected project only in `portal_settings`. Rejected for this slice because URL context is visible, bookmarkable, testable, and avoids hidden state surprises.

2. **Bind tasks through metadata for the first slice.**
   - Project-board-created tasks carry `metadata.connected_project_id`, `metadata.project_root_path`, and `metadata.project_profile`.
   - Board filtering uses `metadata.connected_project_id` for project boards.
   - Alternative: add a `tasks.project_id` column immediately. Deferred because existing task metadata already carries project launch evidence and avoids a broader migration while validating the UX.

3. **Thread project context through task intake and breakdown flows.**
   - The project board estimate form posts to a project-context route or includes a validated project context field handled server-side.
   - Markdown/paste breakdown reviews created from a project board preserve project metadata in `intake_metadata`.
   - Accepted breakdown candidates inherit the same project metadata so every resulting task card remains on the selected project board.
   - Alternative: let accepted candidates rely on later launch-time active project. Rejected because task cards should be project-bound before launch and visible only on the intended board.

4. **Launch validates task/project binding before Worker process creation.**
   - Launch from `/projects/{project_id}/board` or a project-aware endpoint verifies the task is bound to that project.
   - Launch root resolution prefers task metadata root and requires it to match a connected project record.
   - Missing or mismatched project binding returns a workflow/setup error and does not start the Worker Adapter process.
   - Alternative: keep fallback to most-recent connected project. Rejected because it is the direct wrong-repo failure mode.

5. **Keep global pages reachable but not silently launch-capable.**
   - The global dashboard and settings pages remain unchanged.
   - Existing `/board` becomes a redirect/compatibility entry, not an ambiguous global board where launch root can drift.
   - Alternative: keep `/board` as an all-project board with warnings. Rejected for first implementation because it preserves the confusing mental model that caused the demo failure.

## Risks / Trade-offs

- Existing unbound tasks disappear from project boards. → Mitigate by redirecting `/board` safely and, if needed, showing clear copy that existing legacy tasks require rebinding or recreation from a project board.
- Metadata-only binding can be weaker than a relational column. → Mitigate with centralized helpers/tests; add schema migration later only if filtering/querying/reporting pressure proves it necessary.
- Task breakdown/review redirects can lose project context. → Mitigate by using project-aware redirect targets whenever source metadata contains a connected project id.
- Multiple connected projects can still exist. → Mitigate by using explicit URL context for project boards and rejecting launch mismatches instead of relying on recency.
- API clients using global `/estimate` or `/tasks` may create unbound tasks. → Mitigate by preserving APIs but requiring project binding for project-board launch; project-aware endpoints/forms create bound tasks.
