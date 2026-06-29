## 1. Persistence and board filtering

- [x] 1.1 Add minimal task archive helpers that store/remove `metadata.archived_at` without changing `status`, `session_id`, `actual_tokens`, or evidence metadata
- [x] 1.2 Add a helper to archive all unarchived `Done` tasks for one `connected_project_id` only
- [x] 1.3 Update project board task loading/counting so archived tasks are excluded from active board columns
- [x] 1.4 Keep estimation accuracy and Done lifecycle behavior unchanged for archived Done tasks

## 2. Routes and templates

- [x] 2.1 Add authenticated routes/forms for Archive one Done task, Archive all Done tasks for a project, and Unarchive an archived Done task
- [x] 2.2 Add `/projects/{project_id}/task-history` route that returns 404 for unknown projects and lists only tasks bound to the selected project
- [x] 2.3 Add a server-rendered task history template with simple filters for all, active, archived, Done, and Blocked tasks
- [x] 2.4 Update the project board template with per-Done-card Archive buttons, Archive all Done, and a link to project task history

## 3. Verification

- [x] 3.1 Add portal tests proving Mark Done still lands in Done before archive
- [x] 3.2 Add portal tests proving Archive hides a Done task from the board while showing it in project task history with evidence/session links preserved
- [x] 3.3 Add portal tests proving Archive all Done is scoped to the selected project and does not archive non-Done tasks
- [x] 3.4 Add portal tests proving Unarchive returns an archived Done task to the Done board column
- [x] 3.5 Run `openspec validate add-project-task-history-archive --strict`
- [x] 3.6 Run targeted portal tests and `uv run pytest`
