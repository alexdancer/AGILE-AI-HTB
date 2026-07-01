## 1. Data model and helpers

- [x] 1.1 Add `archived_at` and `archived_by` migration/default columns to `connected_projects` without changing existing active projects.
- [x] 1.2 Add project archive helpers: detect archived state, archive project, restore project, and list active/archived projects explicitly.
- [x] 1.3 Update `list_connected_projects()` callers so active surfaces use active projects by default and archived sections request archived/all projects intentionally.

## 2. Portal visibility and actions

- [x] 2.1 Add Archive/Restore project routes with authentication, project lookup, and a running-work/active-queue archive block.
- [x] 2.2 Update `/projects`, `/settings/project`, setup summary, and sidebar context to hide archived projects from active lists and show an explicit archived section or filter.
- [x] 2.3 Update project workspace/direct access for archived projects with an archived banner, Restore action, history/evidence links, and no normal launch encouragement.
- [x] 2.4 Update `/board` default redirect to choose the most recent active project and redirect to `/projects` when only archived projects exist.
- [x] 2.5 Update Open local repo connect behavior so reopening an archived root restores or clearly routes to Restore without creating duplicate project identity.

## 3. Verification

- [x] 3.1 Add/update DB tests for migration defaults, active vs archived listing, archive/restore idempotence, and evidence-preserving archive behavior.
- [x] 3.2 Add/update portal tests for active list hiding, archived section/restore action, archive running-work rejection, direct archived workspace behavior, and `/board` redirect selection.
- [x] 3.3 Run targeted project/archive portal tests.
- [x] 3.4 Run `openspec validate archive-project-visibility --strict`.
- [x] 3.5 Run `uv run pytest`.
