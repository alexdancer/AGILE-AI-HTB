## 1. Parser and Evidence Tests

- [x] 1.1 Add a focused Claude Code native-usage fixture test in `tests/workers/test_adapter_verification.py` using result JSON with `session_id`, `total_cost_usd`, `usage`, `modelUsage`, sentinel output, and cache token fields.
- [x] 1.2 Assert the fixture records `adapter_verification` usage with cache-inclusive prompt tokens, output tokens as completion tokens, `total_tokens`, `cost`, `usage_source=native_usage`, and `tracking_authoritative=true`.
- [x] 1.3 Add a negative test proving Claude Code sentinel/text success without run-bound usage and cost evidence does not become budget-authoritative or board-launchable.

## 2. Native Usage Parser

- [x] 2.1 Extend `_parse_native_usage_evidence()` to parse Claude Code result JSON fields: `session_id`, `usage`, `modelUsage`, `total_cost_usd`, and assistant/result model evidence.
- [x] 2.2 Count Claude cache read and cache creation tokens as prompt-side budget tokens while preserving original cache fields in `raw_usage`.
- [x] 2.3 Resolve Claude model aliases or concrete model names safely enough that a selected alias such as `sonnet` can bind to returned concrete `modelUsage` evidence without accepting unrelated model usage.
- [x] 2.4 Keep nonzero return codes, missing run binding, missing usage, missing model evidence, or missing cost evidence from producing native usage authority.

## 3. Claude Code Adapter Templates and Discovery Boundary

- [x] 3.1 Add or normalize Claude Code native verification and launch templates to use `claude -p --model {model} --output-format stream-json --verbose --max-budget-usd {cap} {prompt}` without Harness Proxy credentials.
- [x] 3.2 Preserve model discovery failure as sanitized discovery evidence and prevent failed stdout/stderr text from being persisted as discovered or allowed model IDs.
- [x] 3.3 Ensure Worker Setup/readiness copy separates Claude Code explicit/curated model selection from native usage verification.

## 4. Launch Accounting

- [x] 4.1 Verify governed Worker launch reuses the shared parser for Claude Code `native_usage` and records cache-inclusive `task_execution` token rows.
- [x] 4.2 Add or update a task-launch test proving Claude Code native launch with result JSON records Worker Run token evidence and enters Review.
- [x] 4.3 Add or update a task-launch test proving Claude Code native launch without trustworthy usage evidence is a recoverable Worker Run failure that returns the Task to Estimated, not Blocked.

## 5. Verification

- [x] 5.1 Run targeted tests for Worker Adapter verification and native Worker launch.
- [x] 5.2 Run `uv run pytest` or the smallest broader suite that covers Worker Adapter setup, launch guardrails, and native usage accounting.
- [x] 5.3 Manually smoke-check the verified Claude command shape with OAuth when available and record only non-secret evidence: sentinel, model, usage fields, `total_cost_usd`, and exit code.
