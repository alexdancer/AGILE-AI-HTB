## Context

Connected projects are persisted in `connected_projects` and currently every project is returned by `db.list_connected_projects()`. The Portal uses that list for `/projects`, `/settings/project`, the sidebar context, setup summary, and `/board` default routing. Done task archive already uses metadata visibility while preserving lifecycle/evidence; project cleanup needs the same non-destructive shape at the connected-project level.

## Goals / Non-Goals

**Goals:**
- Let operators hide stale repos/projects from active Portal surfaces without deleting project or evidence records.
- Keep archived projects recoverable through an explicit archived section and Restore action.
- Keep direct archived project URLs evidence-safe: show the workspace/history with an archived banner and no normal launch encouragement until restored.
- Keep default board routing and setup summaries focused on active projects only.
- Prevent archiving while selected-project work is Running or queue automation is active.

**Non-Goals:**
- No hard delete or filesystem repo deletion.
- No new project-history table.
- No Worker Adapter, model routing, task lifecycle, or token-accounting changes.
- No SPA, drag/drop, websocket, or broader project-management rewrite.

## Decisions

### Use `connected_projects.archived_at` for visibility state

Add nullable archive metadata directly to connected projects, with optional `archived_by` if the existing style needs it. This mirrors task archive semantics and avoids overloading `capability_json`, which is launch/readiness evidence, not UI visibility.

Alternative considered: storing archive state in `capability_json`. Rejected because capability should remain execution readiness, and hiding projects is an operator visibility concern.

### Make active project listing the default

The common list path should return active projects by default, with an explicit `include_archived` or archived-specific helper for settings/archive sections. This is the smallest way to make sidebar, `/projects`, setup summary, and `/board` stop seeing archived projects without duplicating filters everywhere.

Alternative considered: filtering separately in every route/template. Rejected because it is easier to miss a surface and keep stale projects visible.

### Preserve direct archived project access

Archived projects remain addressable by id. The workspace should show an archived banner and Restore action; history stays available. Board/launch surfaces should either be read-only/restore-first or clearly route the operator to restore before launch. This preserves auditability without making archived projects look active.

Alternative considered: returning 404 for archived projects. Rejected because operators need to recover and audit old project history.

### Block archive during active execution

Archive requests should reject when the project has Running tasks, active Worker Runs, or running queue automation. Archive is visibility-only, but hiding a project with active execution is confusing and risks burying live evidence.

Alternative considered: allow archive any time. Rejected because Running work needs visible operator attention.

### Re-open same root path restores or exposes restore

`/settings/project/connect` already upserts by unique `root_path`. If the matching row is archived, the connect flow should not create duplicates. It should restore the archived project or return a clear restore path; the Portal path can prefer direct restore because the operator just asked to open that repo.

Alternative considered: leave archived rows hidden and insert a new row. Rejected because `root_path` is unique and duplicate project history would split evidence.

## Risks / Trade-offs

- Existing tests may assume `list_connected_projects()` returns all rows → update callers/tests to request archived rows only where needed.
- Direct archived board behavior can drift into a second workflow → keep it restore-first and avoid new board states.
- Setup pages may need both active and archived lists → use explicit helper/API parameter rather than ad hoc SQL.
- Migration must preserve all current projects as active by default → nullable `archived_at` and no backfill needed.
