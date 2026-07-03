## 1. Persistence and routing

- [x] 1.1 Extend the existing task archive helper to allow `Estimated` tasks while preserving status and metadata evidence.
- [x] 1.2 Keep archive rejection for `Running`, `Review`, and unsupported statuses with updated operator-facing error copy.

## 2. Project board UI

- [x] 2.1 Add a per-card `Dismiss` form/button for `Estimated` cards on `/projects/{project_id}/board` that uses the existing project-scoped archive route.
- [x] 2.2 Ensure dismissed Estimated tasks disappear from the active board and remain counted only through history/archive visibility.

## 3. Task history restore

- [x] 3.1 Verify project task history shows dismissed Estimated tasks under archived history with lifecycle status and estimate/model evidence preserved.
- [x] 3.2 Verify Unarchive removes archive metadata and returns the task to the Estimated board column.

## 4. Tests and validation

- [x] 4.1 Add/update focused tests for dismissing one Estimated project-board card, preserving `Estimated` status and evidence.
- [x] 4.2 Add/update focused tests that Running/Review tasks cannot be archived/dismissed.
- [x] 4.3 Run targeted portal/database tests, `openspec validate dismiss-estimated-task-cards --strict`, and `uv run pytest`.
