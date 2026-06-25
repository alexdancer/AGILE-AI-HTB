## ADDED Requirements

### Requirement: Claude Code discovery is separate from native usage tracking
The system SHALL treat Claude Code model discovery as separate from Claude Code native usage verification and SHALL allow explicit or curated Claude Code models to be verified for `native_usage` even when native model discovery is unavailable or fails.

#### Scenario: Claude Code discovery failure does not block explicit native verification
- **WHEN** Claude Code model discovery fails or is unsupported
- **AND** the operator has selected an explicit or curated Claude Code model for verification
- **THEN** the system may run Claude Code native usage verification for that selected model
- **AND** discovery failure SHALL NOT by itself mark Claude Code native usage tracking unavailable

#### Scenario: Claude Code discovery failure is not parsed as a model
- **WHEN** a Claude Code discovery command exits nonzero or emits an authentication/error message
- **THEN** the system SHALL record sanitized discovery failure evidence
- **AND** the system SHALL NOT persist the failure text as a discovered or allowed Worker model identifier

#### Scenario: Claude Code model inventory remains explicit or curated
- **WHEN** Claude Code native model discovery is unavailable
- **THEN** the Worker Setup UI SHALL distinguish explicit or curated Claude Code model choices from discovered model inventory
- **AND** Launch Guardrails SHALL still require the selected model to be operator-approved for the Claude Code adapter before normal governed launch
