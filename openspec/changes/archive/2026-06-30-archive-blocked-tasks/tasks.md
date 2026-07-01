## 1. Archive Semantics

- [x] 1.1 Update task archive validation to allow `Done` and `Blocked` lifecycle statuses while still rejecting `Estimated`, `Running`, `Review`, and unsupported active statuses.
- [x] 1.2 Preserve existing archive metadata behavior (`archived_at`, `archived_by`) without changing task status, evidence metadata, session links, Worker Run links, actual tokens, or estimates.

## 2. Board and History UI

- [x] 2.1 Add a per-card Archive action for project-scoped Blocked cards on the AGILE Board.
- [x] 2.2 Keep “Archive all Done” scoped to Done tasks only; do not add bulk Blocked archive controls.
- [x] 2.3 Update project task history so archived Blocked tasks show their Blocked lifecycle status, archived badge/timestamp, and available evidence links/details.
- [x] 2.4 Allow Unarchive from task history for any archived task, including Blocked, while preserving the task lifecycle status.
- [x] 2.5 Update user-facing validation/copy that currently says only Done tasks can be archived to say only Done or Blocked tasks can be archived.

## 3. Tests and Verification

- [x] 3.1 Add portal coverage showing archiving a Blocked project task hides it from the active board, preserves `status="Blocked"`, and keeps blocked/evidence metadata intact.
- [x] 3.2 Add portal coverage showing archived Blocked tasks appear in project task history and can be unarchived back to the Blocked column.
- [x] 3.3 Update the existing archive rejection test so Estimated, Running, and Review tasks remain non-archivable.
- [x] 3.4 Run targeted portal board tests and the full pytest suite.
- [x] 3.5 Run OpenSpec validation for `archive-blocked-tasks` before marking tasks complete.
