## Why

Task Breakdown can fail even when the Control Plane connection test succeeds because the live breakdown request is larger and uses provider-specific request parameters that Anthropic models now reject. Recent local evidence showed `claude-opus-4-8` failing with HTTP 400 for deprecated `temperature`, while `claude-sonnet-5` reached the provider but timed out on the full 12k+ character breakdown request.

## What Changes

- Stop forwarding `temperature` to Anthropic Messages API requests from the shared Control Plane LLM adapter.
- Preserve OpenAI/OpenAI-compatible request behavior; this is not a Worker Adapter change.
- Add Task Breakdown-specific timeout/reporting behavior so timeout failures identify the model, configured timeout, source size, and output budget without exposing secrets or prompt contents.
- Make the Task Breakdown provider timeout and output budget explicit and testable, rather than relying only on a generic provider request timeout.
- Keep the existing manual-candidate fallback after breakdown failure.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `task-breakdown-review`: Task Breakdown Agent failures must distinguish Anthropic parameter compatibility failures from large-request timeout failures, and timeout diagnostics must be safe and actionable.
- `direct-provider-model-clients`: Anthropic Control Plane requests must use the direct Anthropic Messages API without forwarding unsupported OpenAI-style parameters such as `temperature`.
- `control-plane-model-connection`: Task Breakdown Model calls must keep provider-specific structured-output behavior explicit, including timeout and output-budget evidence for large breakdown requests.

## Impact

- Affected code:
  - `src/agile_ai_htb/llm.py` Anthropic request translation and timeout handling.
  - `src/agile_ai_htb/task_breakdown.py` request construction and failure reporting.
  - Task Breakdown route/UI tests and LLM adapter tests.
- Affected behavior:
  - Anthropic models no longer receive `temperature` from Control Plane calls.
  - Opus 4.8-style HTTP 400 `temperature is deprecated` failures should stop.
  - Sonnet 5-style read timeouts should remain failures, but with clearer safe diagnostics and configurable limits.
- Non-goals:
  - No Worker Adapter changes.
  - No model picker redesign.
  - No retries, repair parser, streaming breakdown, or deterministic Markdown fallback in this slice.
  - No storage of secrets or prompt/source text in error diagnostics.
