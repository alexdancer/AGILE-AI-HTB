## ADDED Requirements

### Requirement: OpenRouter control-plane provider

The system SHALL accept `openrouter` as a Control Plane provider that routes through the
existing OpenAI-compatible transport, so an operator can reach many models with a single
OpenRouter API key without new provider-specific code paths. Direct `openai`, `anthropic`, and
`openai-compatible` providers SHALL remain available and unchanged.

#### Scenario: OpenRouter provider accepted and routed

- **WHEN** the operator saves Control Plane settings with provider `openrouter`
- **THEN** the system SHALL accept the provider value as valid
- **AND** subsequent Control Plane requests SHALL be sent over the OpenAI-compatible chat-completions transport

#### Scenario: Default OpenRouter base URL

- **WHEN** provider `openrouter` is configured and no base URL is set
- **THEN** the system SHALL default the base URL to `https://openrouter.ai/api/v1`
- **AND** an explicitly configured base URL SHALL override that default

#### Scenario: Default OpenRouter key env name

- **WHEN** the operator selects provider `openrouter` without specifying an API key env name
- **THEN** the system SHALL default the control-plane API key env name to `OPENROUTER_API_KEY`
- **AND** the pasted key SHALL be stored in ignored local secret storage under that name, never in `.foreman/config.toml`

#### Scenario: OpenRouter appears in the curated model list

- **WHEN** the authenticated control-plane state read and the React Control Plane Settings view render curated choices for provider `openrouter`
- **THEN** both SHALL show an OpenRouter recommended shortlist derived from the single authoritative curated source
- **AND** the existing custom-model path SHALL remain available for OpenRouter model IDs not in the shortlist

#### Scenario: OpenRouter tokens tracked as control-plane usage

- **WHEN** a Control Plane request to an OpenRouter model completes with an OpenAI-shaped `usage` object
- **THEN** the system SHALL record prompt, completion, and total token counts as control-plane/Orchestration Token usage through the existing usage path

### Requirement: Provider-reported control-plane usage cost

The system SHALL prefer a provider-reported per-call cost for Control Plane usage when the
response includes one, and SHALL fall back to the existing computed price otherwise, so cost
accounting is truthful for providers that report cost without regressing providers that do not.
Because Control Plane and proxy-governed Worker turns share `token_turns`, unresolved-cost
persistence SHALL be nullable at every scoped caller while token accounting remains unchanged.

#### Scenario: Reported cost is used when present

- **WHEN** a Control Plane response includes a `usage.cost` value
- **THEN** the system SHALL record that reported cost as the usage cost for the call
- **AND** SHALL NOT overwrite it with a token-multiplied estimate

#### Scenario: Computed fallback when no reported cost

- **WHEN** a Control Plane response does not include a reported cost
- **THEN** the system SHALL fall back to the existing computed price for known models
- **AND** SHALL record no cost (null) for models it cannot price instead of coercing the unresolved value to zero

#### Scenario: Existing-provider tokens and known-model pricing are unchanged

- **WHEN** a Control Plane request uses provider `openai`, `anthropic`, or `openai-compatible` and the response reports no cost
- **THEN** known models SHALL retain their pre-existing computed prices
- **AND** unpriced models SHALL persist null rather than the legacy zero coercion
- **AND** token accounting SHALL be unchanged

#### Scenario: Proxy-governed Worker cost uses the shared nullable ledger contract

- **WHEN** a proxy-governed Worker response has neither a reported cost nor a known computed price
- **THEN** its `token_turns` row SHALL persist null cost rather than zero
- **AND** Worker token accounting and Worker Adapter behavior SHALL be unchanged

### Requirement: Control-plane usage cost is visible in settings

The system SHALL surface the resolved control-plane usage cost wherever the Control Plane
settings UI already shows control-plane token usage, using the same reported-or-computed
resolution, so an operator can confirm the dollar cost of a control-plane call rather than only
its token counts. When no cost can be resolved, the UI SHALL indicate that cost is unavailable
rather than presenting a misleading zero.

#### Scenario: Connection test records and shows cost

- **WHEN** an authenticated operator runs the Control Plane connection test and the test response resolves a usage cost
- **THEN** the recorded test evidence SHALL include the resolved cost alongside token usage
- **AND** the Control Plane settings page SHALL display that dollar cost next to the token usage for the latest test

#### Scenario: Cost unavailable is labeled

- **WHEN** a control-plane call's cost cannot be resolved because the provider reports no cost and the model is not priced
- **THEN** the settings UI SHALL indicate the cost is unavailable
- **AND** SHALL NOT display `$0.00` as if the call were free

#### Scenario: Cost display never exposes secrets

- **WHEN** the settings page renders control-plane cost and usage evidence
- **THEN** it SHALL continue to redact the control-plane API key value as it does today
