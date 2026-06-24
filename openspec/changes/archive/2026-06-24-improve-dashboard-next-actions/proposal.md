## Why

The dashboard currently reports budget, sessions, and alarms, but it does not tell an operator what to do next. Operators have to infer whether they should configure workers, launch tasks, review completed work, or handle alarms from separate pages.

## What Changes

- Add an operator-focused "next actions" section to the dashboard.
- Surface existing workflow states as actionable links:
  - worker setup required when no launchable Worker adapter is available
  - tasks ready to launch
  - tasks awaiting review
  - critical or open alarms
  - default link to the task board
- Reuse existing pages and routes for the destination actions.
- Keep the dashboard server-rendered and framework-free.
- Do not add drag/drop, live updates, notifications, or a new workflow engine.

## Capabilities

### New Capabilities
- `dashboard-next-actions`: Dashboard guidance that summarizes the operator's next workflow actions from existing setup, task, and alarm state.

### Modified Capabilities

## Impact

- Affected UI: `src/agile_ai_htb/templates/dashboard.html`
- Affected route/view-model logic: `src/agile_ai_htb/routes/portal.py`
- Affected tests: portal/dashboard tests covering action visibility and links
- No API contract changes
- No new dependencies
