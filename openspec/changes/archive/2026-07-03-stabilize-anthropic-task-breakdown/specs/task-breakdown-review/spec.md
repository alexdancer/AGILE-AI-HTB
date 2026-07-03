## ADDED Requirements

### Requirement: Breakdown failure diagnostics are safe and actionable
The system SHALL record Task Breakdown Agent failures with safe diagnostics that distinguish provider rejection from large-request timeout behavior while preserving manual recovery.

#### Scenario: Anthropic parameter rejection creates failed review
- **WHEN** the Task Breakdown Agent provider rejects a request with a sanitized HTTP error such as an unsupported parameter error
- **THEN** the Proposed Task Breakdown record SHALL be marked failed with `manual_required` decision
- **AND** the failure message SHALL include the sanitized provider error and model identity when available
- **AND** retry, manual candidate creation, single manual candidate creation, and cancel actions SHALL remain available

#### Scenario: Large Task Breakdown request times out
- **WHEN** the Task Breakdown Agent request times out before a complete provider response is received
- **THEN** the Proposed Task Breakdown record SHALL be marked failed with `manual_required` decision
- **AND** the failure message SHALL include safe diagnostics for model, timeout seconds, source character length, and max output tokens
- **AND** the failure message SHALL NOT include raw source text, prompt text, API keys, or secret values
- **AND** retry, manual candidate creation, single manual candidate creation, and cancel actions SHALL remain available

#### Scenario: Connection test success is not treated as breakdown success
- **WHEN** the Control Plane connection test has recorded success for a model
- **AND** a later Task Breakdown Agent request fails because of provider parameter rejection or timeout
- **THEN** the Task Breakdown review SHALL show the Task Breakdown failure state
- **AND** it SHALL NOT present the prior connection test as proof that the full breakdown request succeeded
