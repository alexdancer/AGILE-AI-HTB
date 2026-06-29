## Context

Project tasks already carry lifecycle state in `tasks.status`, project binding in `tasks.metadata_json`, and Worker/session evidence through existing task/session/run relationships. Done cards currently remain on the project board forever, which preserves evidence but makes the active board noisy.

The requested behavior is not a new lifecycle state: operators still mark Review tasks Done, then archive Done cards later. Archive means "remove from active board, keep in repo task history."

## Goals / Non-Goals

**Goals:**
- Keep the board focused on active/unarchived work.
- Add a separate project task history/archive page for all repo tasks.
- Let operators archive one Done card, archive all Done cards, and unarchive archived Done cards.
- Preserve Done status, actual tokens, Worker Run/session evidence, and estimation accuracy.

**Non-Goals:**
- No hard deletion.
- No new `Archived` task status.
- No new archive table for the first slice.
- No SPA, drag/drop rewrite, or board workflow rewrite.
- No detailed per-action audit log unless a later requirement asks for event history.

## Decisions

### Store archive state in task metadata
Use `task.metadata.archived_at` as the current archive visibility flag. Keep `status = "Done"` for archived Done tasks.

Alternatives considered:
- Add an `Archived` status: rejected because archive is board visibility, not lifecycle.
- Add an `archived_tasks` table: rejected because tasks are already the history records.
- Add a dedicated `archived_at` column now: deferred until query performance or filtering ergonomics prove metadata is insufficient.

### Add a project task history page, not another board column
Use `/projects/{project_id}/task-history` as the separate page. It lists tasks bound to that repo and offers simple filters such as all, active, done, archived, and blocked.

Alternatives considered:
- Keep archived cards in a hidden board section: rejected because the user asked for a separate page.
- Make archive a sixth board column: rejected because it keeps completed clutter in the board workflow.

### Archive actions are server-rendered forms
Add per-card Archive on Done cards and Archive all Done for the selected project board. Add Unarchive on archived Done entries in task history. Use normal POST/redirect behavior and existing auth, not new client state.

Alternatives considered:
- JavaScript-only archive controls: rejected because forms are enough and easier to test.
- Bulk selection UI: deferred until operators need selective multi-archive beyond per-card and archive-all.

## Risks / Trade-offs

- Metadata filtering can become awkward for large datasets → add a real `archived_at` column later if task counts justify it.
- Archive all Done could hide more than intended → scope it to the selected project and unarchived Done tasks only, and keep Unarchive available from history.
- History page can become noisy → start with simple filters; add search only if usage proves it is needed.
