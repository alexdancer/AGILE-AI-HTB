## MODIFIED Requirements

### Requirement: Provider-compatible Task Breakdown structured output
The system SHALL normalize provider-specific structured-output response wrappers for Task Breakdown Agent calls while preserving strict validation of the resulting Proposed Task Breakdown object.

#### Scenario: Claude returns fenced JSON for task breakdown
- **WHEN** the configured Task Breakdown Model is a direct Anthropic/Claude control-plane model
- **AND** the provider response content is a single fenced JSON block containing a complete Proposed Task Breakdown object
- **THEN** the system parses the fenced JSON content
- **AND** validates it with the existing Task Breakdown schema before creating a Proposed Task Breakdown review

#### Scenario: Claude task breakdown requires enough output tokens
- **WHEN** the Task Breakdown Agent calls a direct Anthropic/Claude control-plane model
- **THEN** the request includes an explicit completion-token cap of at least 16,384 tokens for the required Proposed Task Breakdown JSON object
- **AND** the cap is scoped to Task Breakdown Agent calls rather than changing unrelated control-plane requests

#### Scenario: Invalid or truncated provider output remains failed breakdown
- **WHEN** a Task Breakdown Model response is malformed, incomplete, truncated, or does not decode to an object that satisfies the Task Breakdown schema
- **THEN** the system records a breakdown-failed/manual recovery state
- **AND** it does not silently create deterministic Markdown-split tasks
- **AND** it does not create an oversized whole-source Estimated Task without operator action

#### Scenario: Worker model configuration remains separate
- **WHEN** stabilizing direct Anthropic/Claude Task Breakdown Agent parsing
- **THEN** the system does not change Worker Adapter model discovery, Worker launch commands, or Worker execution model selection
