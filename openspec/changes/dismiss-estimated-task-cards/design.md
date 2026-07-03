## Context

The project board already hides archived tasks through `metadata.archived_at`, and project task history already exposes archived tasks with restore controls. Today the archive action is limited to Done and Blocked cards, so an unwanted Estimated card remains on the active launch queue unless the operator launches it, blocks it later, or edits data outside the UI.

## Goals / Non-Goals

**Goals:**

- Let an operator remove one unarchived `Estimated` card from a selected project board.
- Preserve `status = "Estimated"`, estimate/model metadata, launch diagnostics, and orchestration evidence.
- Reuse existing archive visibility and unarchive behavior.
- Keep the UI label operator-friendly: `Dismiss` on Estimated cards, not a new lifecycle state.

**Non-Goals:**

- No bulk dismiss action.
- No hard delete.
- No new `Dismissed` or `Archived` status.
- No schema/table migration.
- No global board behavior change beyond existing project-board redirects.
- No SPA, drag/drop, or board workflow rewrite.

## Decisions

- **Reuse archive metadata for Estimated dismissal.** Existing `metadata.archived_at` already means "hide from active board, keep in history". Reusing it is smaller and preserves the lifecycle/status split.
  - Alternative: add a `dismissed_at` metadata key. Rejected because it duplicates archive visibility behavior and would require parallel filters/unarchive semantics.
  - Alternative: delete the task. Rejected because estimation and orchestration evidence should remain auditable.

- **Expose the action as `Dismiss` only on Estimated cards.** The implementation can route through the existing archive endpoint/persistence, but the board label should match the operator intent: remove this unlaunched card from the active launch queue.
  - Alternative: label it `Archive`. Rejected for Estimated cards because archive reads like completed/history cleanup; `Dismiss` better describes declining a launch candidate.

- **Keep unarchive as the restore path.** Project task history already has Unarchive. Restoring a dismissed Estimated task should remove archive metadata and return it to the Estimated column.
  - Alternative: add a special `Undismiss` button. Rejected as extra UI vocabulary for the same visibility toggle.

## Risks / Trade-offs

- **Risk: Dismissed Estimated tasks look like ordinary archived tasks in history.** → Mitigation: history already shows lifecycle status; tests should assert the task remains `Estimated` and is restorable.
- **Risk: Operators accidentally hide launchable work.** → Mitigation: per-card only; no bulk Estimated dismiss in this slice.
- **Risk: Archive helper wording becomes stale if it still says only Done/Blocked.** → Mitigation: update validation/error copy and tests with the exact allowed statuses.
