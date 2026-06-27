## Context

`build_session_artifact()` in `db.py` already returns `checkpoint_results` — an array of objects with `name`, `passed` (bool), `details` (dict), and `created_at`. The `session_report` route already calls `build_session_artifact()` and passes the full artifact to `session_report.html`. The template already renders token logs, tool traces, alarms, and guardrail snapshots — but not checkpoints.

## Goals / Non-Goals

**Goals:**
- Add a "Checkpoints" section to `session_report.html` when checkpoint results exist
- Show each checkpoint with name, pass/fail pill (green/red), and details summary
- Zero new routes, zero new DB queries, zero new Python code

**Non-Goals:**
- Re-evaluating or recomputing checkpoints
- Interactive checkpoint drill-down
- Historical checkpoint comparison across sessions

## Decisions

### 1. Render directly from existing artifact data

The session report template already receives `artifact` containing `checkpoint_results`. No route changes needed.

### 2. Section placement: after alarms, before bottom of page

Follow the existing section order: token summary → sessions → token log → tool trace → alarms → **checkpoints**. Consistent with the logical sequence (alarms are session-boundary signals, checkpoints are session-boundary evaluations).

### 3. Pass/fail display: green/red pill

Reuse existing `.pill.green` and `.pill.red` CSS classes. Detail keys are displayed as key=value pairs (compact, same pattern as worker run event summaries).

### 4. Skip section entirely when empty

When `artifact.checkpoint_results` is empty or absent, the section is not rendered (consistent with other conditional sections in the template).

## Risks / Trade-offs

- **[Risk] Checkpoint details may contain large nested objects** → Mitigation: Render `json.dumps()` or key=value pairs; details are typically small (e.g., `{"spent": 1600, "cap": 5000}`). Cap at 500 chars per detail block.
