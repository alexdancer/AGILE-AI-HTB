## ADDED Requirements

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
