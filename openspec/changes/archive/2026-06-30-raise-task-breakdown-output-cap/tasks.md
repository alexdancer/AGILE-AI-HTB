## 1. Task Breakdown Cap

- [x] 1.1 Raise the Task Breakdown Agent request cap to 16,384 tokens in `src/agile_ai_htb/task_breakdown.py` without changing unrelated control-plane request defaults.
- [x] 1.2 Confirm the Anthropic request adapter still forwards the task-breakdown-scoped cap through `max_tokens`.

## 2. Regression Coverage

- [x] 2.1 Update the existing Task Breakdown request-cap regression to require at least 16,384 outgoing completion tokens.
- [x] 2.2 Keep or add regression coverage proving truncated/incomplete JSON still creates a `TaskBreakdownValidationError` rather than repaired tasks.
- [x] 2.3 Run focused Task Breakdown/estimator tests.

## 3. Verification

- [x] 3.1 Run `openspec validate raise-task-breakdown-output-cap --strict`.
- [x] 3.2 Run `uv run pytest tests/evals/test_estimator.py -q`.
- [x] 3.3 If local Anthropic credentials are configured, rerun a sanitized live Task Breakdown smoke on the DEMO 2099 source and confirm `finish_reason=end_turn` with valid candidates.
