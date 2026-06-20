## Context

AGILE-AI-HTB currently uses LiteLLM as the single upstream model abstraction for control-plane calls and harness proxy forwarding. The actual wrapper is thin: `LLMClient.acompletion()` delegates to `litellm.acompletion(**request)`, and `calculate_cost()` delegates to `litellm.completion_cost()`.

That creates three problems:

1. It hides the real upstream API path behind a broad abstraction the product does not need.
2. It forces env-var key bridging in app startup so LiteLLM can discover provider keys.
3. It makes the Worker Harness story easier to confuse with control-plane model auth.

The architecture already separates model responsibilities:

```text
AGILE-AI-HTB control plane
  - task estimation
  - recommendations
  - reports
  - proxy upstream forwarding

Worker Harnesses
  - OpenCode / Claude Code / Codex / Hermes
  - native model discovery
  - proxy-governed usage, native usage import, or observed-only evidence
```

This change keeps that split and removes LiteLLM from the implementation.

## Goals / Non-Goals

**Goals:**

- Remove LiteLLM from runtime dependencies.
- Provide explicit direct provider clients for OpenAI-compatible chat completions and Anthropic Messages API.
- Preserve the harness proxy's OpenAI-compatible `/v1/chat/completions` endpoint for Worker tools.
- Preserve usage extraction and token-ledger persistence for non-streaming and streaming responses.
- Keep provider API keys explicit and scoped to the configured control-plane/upstream provider.
- Keep Worker Harness native auth separate from control-plane credentials.
- Update UI/docs/tests so LiteLLM is no longer described as the transport or accounting authority.

**Non-Goals:**

- Do not add a frontend framework or UI redesign beyond copy/settings needed for this provider change.
- Do not implement a full universal provider abstraction layer.
- Do not add provider billing API integration.
- Do not make dollar-cost accounting a launch blocker.
- Do not collapse Worker Harness model selection into control-plane provider settings.
- Do not remove native Worker usage import or observed-only classification.

## Decisions

### Decision: Replace LiteLLM with small provider clients

Create direct provider clients behind the existing `LLMClient` boundary. The boundary should accept the OpenAI-shaped request currently used by the proxy/control-plane call sites and route it based on explicit provider settings.

Initial providers:

- `openai`: OpenAI chat-completions compatible API using `POST /v1/chat/completions`.
- `openai-compatible`: configurable `base_url` using the same OpenAI chat-completions request/response shape.
- `anthropic`: Anthropic Messages API using request/response translation.

Rationale: this covers the user's stated need — "connect to a model with an API like OpenAI, Anthropic and such" — without a heavyweight middle layer.

Alternative considered: keep LiteLLM and hide it better. Rejected because the current pain is the unnecessary dependency and provider-key behavior itself.

### Decision: Preserve the harness proxy API shape

The local harness proxy remains OpenAI-compatible at `/v1/chat/completions` even when the upstream provider is Anthropic. Worker tools can keep using the same base URL and session-scoped bearer key.

```text
Worker CLI
  │ OpenAI-shaped request + session key
  ▼
AGILE proxy /v1/chat/completions
  │ governance transforms + token ledger
  ▼
direct provider client
  ├─ OpenAI-compatible upstream
  └─ Anthropic Messages upstream translation
```

Rationale: the proxy API shape is the integration contract for coding tools. Removing LiteLLM should not make workers learn provider-specific APIs.

Alternative considered: expose provider-native proxy endpoints. Rejected as unnecessary for this change and more disruptive to Worker adapters.

### Decision: Make provider config explicit

Use explicit AGILE settings for the control-plane/upstream provider:

- `AGILE_AI_HTB_CONTROL_PROVIDER`
- `AGILE_AI_HTB_CONTROL_MODEL`
- `AGILE_AI_HTB_CONTROL_API_KEY`
- optional provider endpoint/base URL setting for OpenAI-compatible providers

Keep `TOKEN_TRACKER_*` aliases only where existing compatibility requires it. Remove startup behavior that copies one key into every provider-specific env var.

Rationale: copied keys blur boundaries and can accidentally expose one provider credential to unrelated provider clients.

Alternative considered: continue supporting generic `PROVIDER_API_KEY` as the main path. Rejected because it recreates the same ambiguity the control-plane/Worker split was meant to remove.

### Decision: Treat token usage as authoritative, cost as optional

Provider responses that include usage fields must still be extracted and persisted. Cost calculation should return `None`/zero unless an explicit local pricing table supports the configured model.

Rationale: budget governance in this project is token-first. LiteLLM pricing data is convenient but not required for launch safety.

Alternative considered: immediately recreate LiteLLM's model pricing catalog. Rejected as high-maintenance and not required to remove the dependency.

### Decision: Keep Worker tracking modes distinct

This change does not alter the meaning of tracking modes:

- `proxy_governed`: Worker calls the harness proxy with a session-scoped key; AGILE records upstream usage.
- `native_usage`: Worker uses its own native auth/config; AGILE imports trustworthy usage evidence.
- `observed_only`: Worker can be launched/observed, but usage is not budget-authoritative for governed launch.

Rationale: removing LiteLLM from the proxy does not mean all Worker auth should become direct provider auth.

Alternative considered: make all Workers use the same direct provider clients. Rejected because local coding harnesses have their own native auth, model inventory, and CLI behavior.

### Decision: Keep tests provider-client focused

Tests should mock the HTTP boundary or provider client boundary, not LiteLLM internals. Existing tests that monkeypatch `llm.litellm` should become tests for:

- request forwarding for OpenAI-compatible client
- Anthropic request/response translation
- usage extraction from OpenAI-compatible and Anthropic-shaped responses
- streaming usage preservation
- absence of provider-key env bridging

## Risks / Trade-offs

- Provider translation bugs could break Anthropic proxy mode → Mitigate with focused translation tests and simple first-pass request mapping.
- Streaming formats differ by provider → Mitigate by supporting OpenAI-compatible streaming first and adding Anthropic streaming only if the implementation can preserve usage reliably.
- Cost display may regress for models previously priced by LiteLLM → Mitigate by labeling cost unknown while keeping token counts authoritative.
- Legacy deployments may rely on `PROVIDER_API_KEY` → Mitigate with a compatibility fallback for the control plane only, clearly labeled and without env-var fan-out.
- Direct provider clients can grow into another abstraction layer → Mitigate by keeping only the provider methods used by the harness, not building a generic SDK replacement.

## Migration Plan

1. Add direct provider client implementation and tests while preserving the `LLMClient` call boundary.
2. Switch app startup to construct/configure `LLMClient` from explicit settings.
3. Remove provider-key fan-out from lifespan startup.
4. Update proxy/control-plane tests to use direct client behavior and usage extraction.
5. Remove the `litellm` dependency from `pyproject.toml`.
6. Update UI/docs/demo copy from LiteLLM language to direct provider/proxy language.
7. Run the full pytest suite.

Rollback strategy: because the proxy route boundary remains `/v1/chat/completions`, rollback is limited to restoring the LiteLLM-backed `LLMClient`, dependency, and key-bridging behavior if direct provider connectivity fails during deployment.

## Open Questions

- Should Anthropic streaming be implemented in the first pass, or should Anthropic initially be non-streaming only with clear error messaging for streaming requests?
- Should `openai-compatible` base URL default to the official OpenAI endpoint when omitted, or should `openai` and `openai-compatible` stay separate provider identifiers?
- Which provider/model pairs should receive first-class local pricing table entries, if any?
