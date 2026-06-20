## Why

LiteLLM has become unnecessary abstraction for AGILE-AI-HTB's model connectivity. The harness should make direct provider API calls for its own control-plane/proxy work while preserving the existing separation between control-plane model auth and Worker Harness model/auth.

This removes confusing provider-key bridging behavior, reduces runtime dependencies, and makes the deployable harness story easier to explain: AGILE-AI-HTB connects directly to OpenAI-compatible and Anthropic-style APIs; Worker Harnesses remain governed through proxy, native usage import, or observed-only evidence rules.

## What Changes

- **BREAKING** Remove LiteLLM as a runtime dependency and provider abstraction.
- Replace the thin LiteLLM wrapper with explicit first-party provider clients for OpenAI-compatible chat completions and Anthropic Messages API.
- Keep the harness proxy's `/v1/chat/completions` surface for Worker tools, but route upstream through direct provider clients instead of LiteLLM.
- Stop copying the control-plane API key into unrelated provider-specific env vars such as `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`.
- Treat `AGILE_AI_HTB_CONTROL_PROVIDER`, `AGILE_AI_HTB_CONTROL_MODEL`, and `AGILE_AI_HTB_CONTROL_API_KEY` as the canonical control-plane connection configuration.
- Keep Worker Harness auth/model selection separate from control-plane provider settings.
- Keep proxy-governed, native-usage, and observed-only Worker modes distinct.
- Make token usage tracking mandatory where provider responses include usage; treat dollar cost as optional/unknown unless a direct pricing table is available.
- Update UI/docs/tests that currently describe proxy-governed mode or the control plane as LiteLLM-based.

## Capabilities

### New Capabilities
- `direct-provider-model-clients`: Direct provider clients for AGILE-AI-HTB control-plane and proxy calls without LiteLLM.

### Modified Capabilities
- `control-plane-model-connection`: Control-plane model setup changes from LiteLLM-provider abstraction to explicit direct provider API configuration.
- `worker-adapter-verification`: Proxy-governed Worker verification remains supported, but the proxy must not expose real provider keys and must use direct provider clients upstream.
- `governed-worker-launch`: Proxy-governed Worker launch keeps the same harness proxy endpoint while removing LiteLLM from upstream request forwarding and usage extraction.

## Impact

- Affected source:
  - `src/agile_ai_htb/llm.py`
  - `src/agile_ai_htb/routes/proxy.py`
  - `src/agile_ai_htb/app.py`
  - `src/agile_ai_htb/settings.py`
  - portal routes/templates that display control-plane and Worker tracking language
- Affected tests:
  - `tests/test_llm_adapter.py`
  - proxy API/streaming tests
  - control-plane settings/connection tests
  - Worker adapter verification tests where proxy-governed copy references LiteLLM
- Affected packaging/docs:
  - `pyproject.toml` dependency list
  - README/operator docs/demo copy mentioning LiteLLM
- Compatibility:
  - Existing session-scoped harness proxy keys remain valid for proxy-governed Worker calls.
  - Legacy `PROVIDER_API_KEY` alias may remain as explicit compatibility fallback for the control plane only, but it must not be bridged into unrelated provider env vars.
  - Cost calculation may become unavailable for unsupported models until an explicit pricing table is added.
