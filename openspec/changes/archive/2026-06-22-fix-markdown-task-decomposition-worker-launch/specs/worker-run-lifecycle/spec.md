## MODIFIED Requirements

### Requirement: Retryable Worker Run failure returns task to Estimated
The system SHALL return a task to Estimated when a background Worker Run fails due to a retryable operational failure, while preserving enough sanitized command evidence for the operator to diagnose launch command, model, tracking mode, stdout, stderr, and return code.

#### Scenario: Timeout returns to Estimated
- **WHEN** a Running task's Worker Run times out after the adapter command started
- **THEN** the system marks the Worker Run `failed`
- **AND** the task returns to Estimated
- **AND** the task card shows retryable timeout evidence
- **AND** the task remains eligible for another launch

#### Scenario: Nonzero exit returns to Estimated
- **WHEN** a Running task's Worker Run exits nonzero without a hard safety violation
- **THEN** the system marks the Worker Run `failed`
- **AND** the task returns to Estimated with sanitized failure evidence
- **AND** the task remains eligible for another launch

#### Scenario: OpenCode return-code-one failure shows command evidence
- **WHEN** an OpenCode Worker Run exits with return code 1
- **THEN** the task returns to Estimated instead of staying Running
- **AND** the task card or metadata preserves sanitized stderr/stdout and the redacted command plan used for that attempt
- **AND** the preserved evidence includes the selected adapter and selected model
