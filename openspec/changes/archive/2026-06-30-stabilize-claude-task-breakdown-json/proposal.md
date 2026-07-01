## Why

Claude control-plane connection verification can pass while Task Breakdown Agent runs still fail, because the breakdown path currently relies on OpenAI-style JSON mode semantics that Anthropic does not enforce. A live repro against the configured Claude control-plane model produced `TaskBreakdownValidationError: task breakdown returned invalid JSON` on 5/5 attempts; the raw response was fenced JSON and, at the current implicit Anthropic cap, truncated at `finish_reason=max_tokens`.

## What Changes

- Make Claude/Anthropic Task Breakdown Agent calls request enough completion tokens for the required structured review payload.
- Accept Claude's common fenced JSON response shape while still validating the parsed object through the existing task-breakdown schema.
- Preserve strict failure behavior for malformed, incomplete, or non-object responses.
- Add regression coverage for Anthropic-style fenced JSON and truncation-sensitive task breakdown behavior.
- Do not change Worker Adapter behavior, Worker model discovery, Control Plane connection-test semantics, or token accounting categories.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `control-plane-model-connection`: Task Breakdown Model behavior must be reliable for direct Anthropic/Claude control-plane models, including provider response shapes that do not support OpenAI JSON mode.

## Impact

- Affected code: `src/agile_ai_htb/task_breakdown.py`, likely `src/agile_ai_htb/llm.py` only if provider-specific request translation needs an explicit Anthropic-safe knob.
- Affected tests: `tests/evals/test_estimator.py`, `tests/unit/test_llm_adapter.py` if request translation behavior changes.
- No new dependencies, routes, schema tables, Worker Adapter changes, or public API shape changes.
