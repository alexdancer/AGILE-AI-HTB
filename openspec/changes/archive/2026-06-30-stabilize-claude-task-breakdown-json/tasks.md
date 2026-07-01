## 1. Regression Tests

- [x] 1.1 Add a deterministic Task Breakdown Agent test that feeds a complete Proposed Task Breakdown object wrapped in a single ```json fenced block and expects `breakdown_task_source` to return a validated `TaskBreakdownResult`.
- [x] 1.2 Add a deterministic Task Breakdown Agent test that captures the LLM request and asserts the request includes an explicit task-breakdown-scoped `max_tokens` value greater than the current implicit Anthropic 1024-token cap.
- [x] 1.3 Add or preserve a negative test proving malformed, incomplete, or non-object task-breakdown content still raises `TaskBreakdownValidationError` and flows to breakdown-failed/manual recovery.

## 2. Task Breakdown Parser and Request Fix

- [x] 2.1 Add a small parser helper in `src/agile_ai_htb/task_breakdown.py` that accepts either bare JSON object text or one complete fenced JSON block, then rejects prose-wrapped, partial, or non-object content.
- [x] 2.2 Use the parser helper inside the existing Task Breakdown response path before `validate_breakdown_result`, without weakening required fields, candidate kind checks, or manual recovery behavior.
- [x] 2.3 Add an explicit bounded `max_tokens` value to Task Breakdown Agent requests only; do not globally raise Anthropic defaults or change unrelated control-plane/proxy calls.

## 3. Verification

- [x] 3.1 Run `uv run pytest tests/evals/test_estimator.py tests/unit/test_llm_adapter.py -q` after implementation.
- [x] 3.2 Run `uv run htb check` to confirm the configured Control Plane still verifies.
- [x] 3.3 Re-run the live Claude task-breakdown repro from diagnosis, or an equivalent local script, and confirm the same small source produces a validated breakdown instead of `TaskBreakdownValidationError`.
- [x] 3.4 Run `openspec validate stabilize-claude-task-breakdown-json --strict`.
- [x] 3.5 Run `uv run pytest` after task checkboxes are updated, unless blocked by unrelated dirty-worktree failures and reported with evidence.

## 4. Cleanup

- [x] 4.1 Remove any temporary diagnosis scripts, raw provider-output dumps, or `[DEBUG-...]` instrumentation before sign-off.
- [x] 4.2 Confirm no secret values from `.htb/secrets.env` or live provider responses are written to tracked files or logs.
