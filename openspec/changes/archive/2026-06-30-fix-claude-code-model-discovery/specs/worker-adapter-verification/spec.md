## MODIFIED Requirements

### Requirement: First-class Worker Adapter presets
The system SHALL expose OpenCode, Claude Code, Codex, and Hermes as first-class Worker Adapter presets while allowing only adapters with verified budget-authoritative tracking modes to launch normal governed tasks. Adapter launch compatibility SHALL be based on operator-approved allowed Worker models, whether the model inventory came from native discovery or a curated adapter inventory.

#### Scenario: Unverified adapter visible but blocked
- **WHEN** a Worker Adapter preset exists but has not passed token-tracking verification
- **THEN** the Portal shows the adapter status and keeps normal governed Launch disabled for that adapter

#### Scenario: Adapter verified in native usage mode
- **WHEN** a Worker Adapter has proven native usage import for at least one operator-approved allowed model
- **THEN** the Portal shows the adapter as native-usage verified and eligible for governed local launch with compatible allowed models

#### Scenario: Claude Code verifies with curated allowed model
- **WHEN** Claude Code model discovery is curated rather than native
- **AND** the operator selects an allowed curated Claude Code model for verification
- **AND** Claude Code emits trustworthy native usage evidence for that model
- **THEN** the Portal shows Claude Code as native-usage verified and eligible for governed local launch with compatible allowed Claude Code models
