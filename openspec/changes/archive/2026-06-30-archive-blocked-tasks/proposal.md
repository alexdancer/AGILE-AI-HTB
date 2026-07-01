## Why

Blocked tasks can accumulate on the AGILE Board after manual review decisions, guardrail blocks, or manual-estimate failures. Operators need a safe way to remove stale Blocked cards from the active board without deleting task evidence or changing the meaning of the `Blocked` lifecycle state.

## What Changes

- Allow project-scoped Blocked task cards to be archived from the AGILE Board using the existing archive visibility mechanism.
- Keep archived Blocked tasks as normal `Blocked` task records with session, Worker Run, token, launch, review, and blocked-reason evidence preserved.
- Show archived Blocked tasks in project task history and allow operators to unarchive them back onto the active board.
- Keep bulk archive scoped to Done tasks only; do not add “Archive all Blocked” in this slice.
- Do not introduce hard delete, an `Archived` lifecycle status, a new archive table, SPA behavior, or workflow/lifecycle rewrites.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project-scoped-board`: extend active-board archive behavior so Blocked cards can be removed from the active project board while preserving `Blocked` status and evidence.
- `project-task-history`: extend history/archive behavior so archived Blocked tasks are visible, restorable, and evidence-preserving like archived Done tasks.

## Impact

- Board/template behavior for project-scoped Blocked cards.
- Task archive validation semantics for allowed lifecycle statuses.
- Project task history restore controls for archived non-Done tasks.
- Portal tests for archiving and unarchiving Blocked tasks.
- No database migration or dependency change expected; reuse task metadata archive state.
