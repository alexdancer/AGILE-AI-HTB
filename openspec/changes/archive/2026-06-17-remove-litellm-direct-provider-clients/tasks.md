## 1. Provider Client Foundation

- [x] 1.1 Inspect current `LLMClient`, proxy route, control-plane connection test, estimator/reporting call sites, and tests to confirm all LiteLLM entry points.
- [x] 1.2 Add direct provider-client abstractions behind the existing `LLMClient` boundary for `openai`, `openai-compatible`, and `anthropic` providers.
- [x] 1.3 Implement OpenAI-compatible chat completions forwarding, including configurable base URL, bearer auth, JSON response handling, and sanitized error handling.
- [x] 1.4 Implement Anthropic Messages API translation for the OpenAI-shaped request fields this harness uses (`messages`, `system` content, `max_tokens`, temperature where present) and normalize responses back to the existing proxy/control-plane usage shape.
- [x] 1.5 Add focused unit tests for provider selection, OpenAI-compatible forwarding, Anthropic translation, missing credentials, and unsupported provider errors.

## 2. Usage, Streaming, and Cost Accounting

- [x] 2.1 Keep `/v1/chat/completions` request/response shape stable for Worker tools.
- [x] 2.2 Route proxy upstream calls through the new `LLMClient` direct-provider path without changing session bearer-token auth, governance transforms, or token-turn persistence.
- [x] 2.3 Preserve OpenAI-compatible streaming proxy behavior with final usage extraction when the upstream stream includes usage.
- [x] 2.4 Define Anthropic streaming behavior for the first implementation pass: either implement usage-preserving streaming or reject streaming Anthropic proxy requests with a clear sanitized error.
- [x] 2.5 Replace LiteLLM cost calculation with optional local pricing behavior that returns unknown/zero when pricing is unavailable without blocking token tracking.
- [x] 2.6 Add tests covering usage extraction, streaming usage preservation or explicit Anthropic streaming rejection, and optional cost behavior.

## 3. Configuration and Startup Cleanup

- [x] 3.1 Change the default control-plane provider from `litellm` to the direct provider identifier chosen for the default model path.
- [x] 3.2 Add explicit settings for direct provider base URL/endpoint where needed while preserving existing `AGILE_AI_HTB_CONTROL_*` and `TOKEN_TRACKER_*` compatibility aliases.
- [x] 3.3 Remove startup provider-key fan-out from `app.py` so the control-plane key is not copied into unrelated provider env vars.
- [x] 3.4 Keep `PROVIDER_API_KEY` compatibility as a control-plane fallback only, with tests proving it is not injected into Worker environments or unrelated provider env vars.
- [x] 3.5 Update control-plane connection test behavior and tests to exercise direct provider clients rather than LiteLLM.

## 4. Proxy-Governed Worker Flow Preservation

- [x] 4.1 Verify `/v1/chat/completions` request/response compatibility remains stable for proxy-governed Worker tools.
- [x] 4.2 Ensure proxy-governed Worker launch/verification injects only the Harness Proxy base URL and session-scoped Harness key into Worker environments.
- [x] 4.3 Update Worker adapter verification tests so proxy-governed verification proves direct-provider upstream usage without assuming LiteLLM.
- [x] 4.4 Verify native-usage and observed-only Worker modes are unchanged by the direct-provider client migration.

## 5. Dependency, Copy, and Documentation Cleanup

- [x] 5.1 Remove `litellm` from `pyproject.toml` runtime dependencies.
- [x] 5.2 Update tests that monkeypatch `llm.litellm` to mock direct provider clients or HTTP boundaries instead.
- [x] 5.3 Update portal UI copy from “Proxy-governed LiteLLM usage” to direct provider/proxy wording.
- [x] 5.4 Update README, demo worker text, code review/docs, and operator setup copy that still describes LiteLLM as the transport or accounting path.
- [x] 5.5 Search the repo for `LiteLLM`, `litellm`, and `LITELLM`; remove or intentionally retain only historical/archive references.

## 6. Verification

- [x] 6.1 Run targeted provider-client, proxy API, proxy streaming, settings, control-plane, and Worker adapter verification tests.
- [x] 6.2 Run the full `pytest` suite.
- [x] 6.3 Run `openspec status --change "remove-litellm-direct-provider-clients"` and confirm the implementation remains aligned with proposal/design/specs.
