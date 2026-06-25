## Why

Claude Code can fail or lack native model discovery while still emitting machine-readable run usage and `total_cost_usd` from `claude -p --output-format json|stream-json --verbose`. AGILE-AI-HTB should use that evidence for budget-authoritative `native_usage` without undercounting Claude cache tokens or confusing discovery failure with tracking failure.

## What Changes

- Add explicit Claude Code native verification and launch command support using non-interactive `claude -p --model {model} --output-format stream-json --verbose` with a bounded `--max-budget-usd` safety cap.
- Extend native usage parsing to accept Claude Code result JSON, including `total_cost_usd`, `usage`, `modelUsage`, `session_id`, and cache token fields.
- Count Claude cache creation/read tokens as prompt-side budget tokens so recorded totals match Claude Code cost evidence instead of only `input_tokens + output_tokens`.
- Keep Claude Code model discovery separate from tracking verification: failed or unavailable `claude models` must not prevent verifying an explicitly selected/curated Claude model for native usage.
- Preserve `observed_only` fallback for Claude Code runs that return text but no trustworthy usage/cost evidence.
- Do not add proxy-governed Claude Code support in this slice.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `worker-adapter-verification`: Claude Code native usage verification accepts run-bound JSON usage/cost evidence and records cache-inclusive verification spend.
- `governed-worker-launch`: Claude Code native-usage launches use non-interactive Claude Code command templates and record cache-inclusive Worker usage from result JSON.
- `native-worker-model-discovery`: Claude Code model discovery failure is not treated as proof that native usage tracking is unavailable for explicitly selected/curated models.

## Impact

- Affected code: `src/agile_ai_htb/worker_adapters.py`, native launch/verification command templates, task launch native usage recording, Worker Adapter setup/readiness copy where Claude discovery and tracking are shown.
- Affected tests: Worker Adapter verification tests for Claude Code result JSON, cache token accounting, wrong/missing usage fallback, and launch recording if existing task-launch tests cover native usage.
- No new runtime dependency.
- No control-plane provider credential changes; Claude Code continues to use its own OAuth/native configuration.
