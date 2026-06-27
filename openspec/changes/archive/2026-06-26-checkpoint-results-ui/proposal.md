## Why

The harness runs 4 checkpoints at session boundaries: budget_health, stuck_loop_score, tool_diversity, and timeout_respect. Results are persisted in `checkpoint_results` and included in `build_session_artifact()`, but the Portal never displays them. Operators reviewing a session report see token logs, tool traces, and alarms — but not checkpoint results. This is a completeness gap: the data exists, the UI doesn't.

## What Changes

- Add a "Checkpoints" section to `session_report.html` below the existing alarm/evidence sections
- Render each checkpoint with: name, pass/fail badge (green/red pill), and details summary
- Use the existing `build_session_artifact()` data — no new route or DB query
- Skip the section entirely when a session has no checkpoint results

## Capabilities

### New Capabilities

- `checkpoint-results-display`: The session report page SHALL display checkpoint results (name, pass/fail, details) when results exist for that session.

### Modified Capabilities

None. Additive only.

## Impact

- `src/agile_ai_htb/templates/session_report.html`: New Checkpoints section (~25 lines Jinja2)
- `tests/portal/test_sessions.py`: 1 new test (session report renders checkpoint results)
