## Why

Claude/Anthropic Task Breakdown currently fails on the small DEMO 2099 Markdown intake because the response is cut off at the task-breakdown completion cap and then fails strict JSON parsing. The control-plane connection is healthy; the failure is structured-output sizing for Task Breakdown Agent calls.

## What Changes

- Raise the Task Breakdown Agent completion-token cap high enough for realistic small-demo Markdown breakdowns.
- Keep the cap scoped to Task Breakdown Agent calls only; do not change global control-plane/provider defaults.
- Preserve strict parsing and manual recovery for malformed, incomplete, or schema-invalid Task Breakdown output.
- Add regression coverage proving the raised cap is sent and truncated JSON still fails cleanly.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `control-plane-model-connection`: clarify that direct Anthropic/Claude Task Breakdown requests must use a bounded cap with enough headroom for the observed small-demo Proposed Task Breakdown JSON.

## Impact

- Affected code: `src/agile_ai_htb/task_breakdown.py`.
- Affected tests: task-breakdown estimator/eval regressions in `tests/evals/test_estimator.py` or the nearest existing Task Breakdown test file.
- No database schema changes.
- No Worker Adapter, Worker model discovery, launch command, proxy, or token-accounting changes.
