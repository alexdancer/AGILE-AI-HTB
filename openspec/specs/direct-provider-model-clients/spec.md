# direct-provider-model-clients Specification

## Purpose
Define the direct upstream provider client layer used by Foreman AI HQ for control-plane model calls and harness proxy forwarding without relying on LiteLLM as a runtime abstraction.
## Requirements
### Requirement: Direct provider model client selection
The system SHALL select a direct upstream provider client from explicit control-plane provider settings without requiring LiteLLM.

#### Scenario: OpenAI provider selected
- **WHEN** `FOREMAN_AI_HQ_CONTROL_PROVIDER` is configured as `openai`
- **THEN** Foreman AI HQ sends model requests directly to the OpenAI-compatible chat completions API using the configured control-plane model and control-plane API key

#### Scenario: OpenAI-compatible provider selected
- **WHEN** `FOREMAN_AI_HQ_CONTROL_PROVIDER` is configured as `openai-compatible` with a compatible base URL
- **THEN** Foreman AI HQ sends OpenAI-shaped chat completion requests directly to that base URL using the configured control-plane model and control-plane API key

#### Scenario: Anthropic provider selected
- **WHEN** `FOREMAN_AI_HQ_CONTROL_PROVIDER` is configured as `anthropic`
- **THEN** Foreman AI HQ sends model requests directly to the Anthropic Messages API using the configured control-plane model and control-plane API key

### Requirement: Direct provider usage extraction
The system SHALL extract provider-reported token usage from direct provider responses and persist it to the token ledger when available.

#### Scenario: OpenAI-compatible usage returned
- **WHEN** an OpenAI-compatible provider response includes `usage.prompt_tokens`, `usage.completion_tokens`, and `usage.total_tokens`
- **THEN** the system records those token counts for the relevant spend category

#### Scenario: Anthropic usage returned
- **WHEN** an Anthropic provider response includes input and output token usage
- **THEN** the system maps those counts to prompt tokens, completion tokens, and total tokens before recording usage

#### Scenario: Provider omits usage
- **WHEN** a provider response does not include usage information
- **THEN** the system records zero or unknown token usage rather than fabricating token counts

### Requirement: Optional cost calculation
The system SHALL treat dollar-cost calculation as optional when using direct provider clients.

#### Scenario: Pricing unavailable
- **WHEN** token usage is recorded for a model without configured pricing data
- **THEN** the system preserves token counts and records cost as unknown or zero without blocking the session solely because cost is unavailable

#### Scenario: Pricing available
- **WHEN** token usage is recorded for a model with configured pricing data
- **THEN** the system may calculate and persist the estimated cost from the local pricing data

### Requirement: No LiteLLM runtime dependency
The system SHALL NOT require LiteLLM to run control-plane model calls, harness proxy forwarding, or token usage accounting.

#### Scenario: Application starts without LiteLLM
- **WHEN** Foreman AI HQ is installed without LiteLLM
- **THEN** the application starts and direct provider model clients remain available

#### Scenario: Tests exercise direct clients
- **WHEN** the test suite verifies model forwarding and usage extraction
- **THEN** tests mock direct provider HTTP/client boundaries rather than LiteLLM APIs

### Requirement: Anthropic request parameter compatibility
The system SHALL translate OpenAI-shaped internal control-plane requests to Anthropic Messages API payloads without forwarding unsupported OpenAI-style request parameters.

#### Scenario: Anthropic request omits temperature
- **WHEN** the configured control-plane provider is `anthropic`
- **AND** the internal model request includes `temperature`
- **THEN** the Anthropic Messages API payload SHALL NOT include `temperature`
- **AND** the request SHALL still include the configured Anthropic model, translated messages, system content when present, and max token budget

#### Scenario: Provider-prefixed Anthropic model omits temperature
- **WHEN** an Anthropic model value includes a provider prefix such as `anthropic/claude-opus-4-8`
- **AND** the internal model request includes `temperature`
- **THEN** the Anthropic Messages API payload SHALL use the provider-stripped model ID
- **AND** the payload SHALL NOT include `temperature`

#### Scenario: OpenAI-compatible providers keep their request behavior
- **WHEN** the configured control-plane provider is `openai` or `openai-compatible`
- **THEN** the system SHALL preserve the provider-specific OpenAI-compatible request translation rules
- **AND** the Anthropic temperature omission rule SHALL NOT be applied to those providers

