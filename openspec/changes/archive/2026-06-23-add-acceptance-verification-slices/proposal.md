## Why

The current Task Breakdown Agent correctly avoids raw Markdown bullet splitting, but demo evidence showed a second failure mode: multi-slice implementation can pass local slice checks while losing the original integrated task contract. We need decomposition to stay central while adding an explicit final Acceptance Verification slice for integrated artifacts.

## What Changes

- Add an explicit candidate kind to Proposed Task Breakdown candidates:
  - `implementation`
  - `acceptance_verification`
- Add one editable `global_contract_summary` to each Proposed Task Breakdown.
- Have implementation candidates inherit the global contract summary and relevant constraints before Task Estimation.
- Auto-propose an Acceptance Verification candidate, recommended last, when a multi-slice breakdown produces one integrated artifact such as a CLI, app, API, demo, or report.
- Keep Acceptance Verification as an ordinary estimated AGILE Board Task with its own budget, Worker Run, and Review Disposition.
- Make Acceptance Verification verification-focused, not a whole-task implementation rerun: it should run the smallest executable proof available and report findings.
- Preserve the first-slice boundary: no board grouping, no hard dependency enforcement, no automatic repair-task creation from failed Acceptance Verification findings.

## Capabilities

### New Capabilities

### Modified Capabilities
- `task-breakdown-review`: Extend Proposed Task Breakdown output, review editing, accepted Task metadata, and decomposition fixtures to support candidate kind, global contract summary, and Acceptance Verification slices.

## Impact

- Affected code:
  - `src/agile_ai_htb/task_breakdown.py`
  - task-breakdown persistence/schema code
  - task intake/review routes and templates
  - accepted Task metadata construction
  - task-breakdown/decomposition tests and golden fixtures
- Affected behavior:
  - Task Breakdown Agent output schema changes.
  - Breakdown review page displays/edits candidate kind and global contract summary.
  - Integrated-artifact breakdowns include an operator-rejectable Acceptance Verification candidate by default.
- No dependency changes expected.
