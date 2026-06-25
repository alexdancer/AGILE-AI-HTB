## 1. Project Board Routing

- [x] 1.1 Add a project-aware board route at `/projects/{project_id}/board` that resolves the connected project, passes `active_project`, and returns 404 for unknown project ids.
- [x] 1.2 Refactor existing board rendering into a shared helper so project board and compatibility routing reuse the same grouping/error/template behavior.
- [x] 1.3 Change `/board` into a safe compatibility entry that redirects to the most-recent connected project board or `/projects` when none exist.
- [x] 1.4 Update `project_workspace.html` and related sidebar/navigation copy so the project overview links to `/projects/{project_id}/board`.

## 2. Project-Bound Task Metadata

- [x] 2.1 Add small server-side helpers for building and validating project task metadata (`connected_project_id`, `project_root_path`, `project_profile`) from a connected project record.
- [x] 2.2 Filter project board tasks by `metadata.connected_project_id` while leaving legacy/unbound tasks off project boards.
- [x] 2.3 Update project board task/estimate form handling so created Estimated tasks inherit selected project metadata and redirect back to `/projects/{project_id}/board`.
- [x] 2.4 Preserve existing non-project API behavior while ensuring unbound tasks cannot silently launch against a different project root.

## 3. Task Breakdown Project Context

- [x] 3.1 Carry selected project metadata into task breakdown `intake_metadata` when markdown/paste intake starts from a project board.
- [x] 3.2 Ensure accepted breakdown candidates inherit project metadata on every created task card.
- [x] 3.3 Make task breakdown accept/retry/manual redirects return to the project board when the source breakdown has a connected project id.

## 4. Launch Project Validation

- [x] 4.1 Update task launch endpoints/routes so project-board launches provide selected project context to `launch_task` or validate it before calling launch.
- [x] 4.2 Update launch root resolution to require valid task project metadata and to use the task-bound root instead of falling back to the most-recent connected project.
- [x] 4.3 Reject missing or mismatched task/project binding before Worker Adapter process creation, preserving retry/correction evidence without mutating the wrong repo.
- [x] 4.4 Record selected project id and task-bound project root in task metadata, Worker Run metadata, command evidence, and Worker timeline events.

## 5. Tests and Verification

- [x] 5.1 Add portal tests for `/projects/{project_id}/board`, unknown project 404, active project sidebar/header context, and `/board` redirect behavior.
- [x] 5.2 Add board filtering tests proving tasks from Project A do not appear on Project B's board.
- [x] 5.3 Add task intake and estimate-form tests proving project-board-created tasks include project metadata and redirect to the selected project board.
- [x] 5.4 Add task breakdown acceptance tests proving project metadata is preserved on all accepted candidate tasks and redirects remain project-aware.
- [x] 5.5 Add launch tests proving mismatched/unbound tasks are rejected before runner invocation and correctly bound tasks launch with the selected project root.
- [x] 5.6 Run targeted tests for project setup, portal board behavior, task API/breakdown flows, and launch/workdir enforcement.
- [x] 5.7 Run full `pytest` before marking OpenSpec tasks complete.
