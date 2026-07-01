## Context

The project board already separates task lifecycle from board visibility for Done tasks: archived tasks remain task records, keep their lifecycle status, and are hidden from active board columns through `metadata.archived_at`. Project task history already lists all project tasks and has filters for active, archived, Done, and Blocked tasks.

Blocked tasks currently have no equivalent board-removal path. That leaves stale manual-estimate failures, review blocks, or hard guardrail blockers visible forever unless the operator changes lifecycle status or edits data outside the Portal.

## Goals / Non-Goals

**Goals:**

- Let operators archive individual project-scoped Blocked cards from the AGILE Board.
- Preserve `status="Blocked"` and all blocked/session/Worker Run/token evidence when archived.
- Let project task history display and unarchive archived Blocked tasks.
- Reuse existing task metadata archive state and active-board filtering.
- Keep implementation small and server-rendered.

**Non-Goals:**

- No hard delete for tasks.
- No new `Archived` lifecycle status.
- No new archive table, task events table, or schema migration.
- No bulk “Archive all Blocked” action in this slice.
- No lifecycle rewrite, board column rewrite, SPA, drag/drop UI, or Worker launch behavior change.

## Decisions

### Reuse task metadata archive state

Use the existing `metadata.archived_at` / `metadata.archived_by` archive state for Blocked tasks. The active board already hides archived tasks independent of lifecycle status, so this keeps the change focused on validation and UI affordances.

Alternative considered: add a first-class `tasks.archived_at` column. Rejected for this slice because current JSON metadata is already used for Done archives and no performance/filtering evidence requires a migration.

### Keep `Blocked` as lifecycle status

Archiving a Blocked task hides it from the active board but does not mark it Done, create an Archived status, or clear blocked evidence. History remains the audit surface for old blockers.

Alternative considered: convert removed Blocked tasks to Done or a new Archived status. Rejected because it would blur lifecycle meaning and could distort review/evidence semantics.

### Per-card archive only for Blocked

Expose Archive on each Blocked card but keep “Archive all Done” unchanged. Blocked cards often represent unresolved safety, setup, or manual-estimate issues, so bulk hiding them could mask live operational problems.

Alternative considered: add “Archive all Blocked.” Rejected for now; it can be reconsidered only if operators need bulk cleanup and accept the risk.

### History restore applies to any archived task

Project task history should render Unarchive for archived Blocked tasks as it does for archived Done tasks. Unarchiving removes archive metadata only; it does not alter lifecycle state.

Alternative considered: make Blocked archives one-way. Rejected because the existing archive model is visibility-only and reversible.

## Risks / Trade-offs

- **Risk:** Operators may archive a Blocked task that still represents a real issue. → **Mitigation:** keep this per-card only, preserve history, and retain the Blocked status in task history.
- **Risk:** Existing copy may imply only Done tasks can be archived. → **Mitigation:** update board/history specs, validation messages, and tests to say Done or Blocked where appropriate.
- **Risk:** Archived Blocked tasks could be missed in normal board scans. → **Mitigation:** keep the History/Archived counts and blocked/history filters discoverable from the board toolbar.
