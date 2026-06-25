## ADDED Requirements

### Requirement: Worker Run lifecycle includes timeline evidence
The system SHALL include Worker Run timeline events as part of lifecycle evidence for launch, running, review, completion, and retryable operational failure states.

#### Scenario: Failed Worker Run has lifecycle timeline
- **WHEN** a Worker Run fails due to timeout, nonzero adapter exit, missing usage evidence, or workdir mismatch
- **THEN** the Worker Run lifecycle evidence includes timeline events that show the launch attempt, failure class, retryability, and sanitized diagnostic details
- **AND** the associated task remains in the lifecycle state required by the existing Worker Run failure requirements

#### Scenario: Completed Worker Run has review timeline
- **WHEN** a Worker Run completes and moves the task to Review
- **THEN** the Worker Run lifecycle evidence includes timeline events for successful adapter completion and required usage/file evidence capture

### Requirement: Worker Run lifecycle includes repo-context evidence
The system SHALL preserve Repo Context Brief evidence on Worker Runs associated with a connected project.

#### Scenario: Review shows launch context
- **WHEN** an operator reviews a completed Worker Run for a connected project
- **THEN** the lifecycle evidence includes the Repo Context Brief source list and bounded brief content
- **AND** the evidence is available alongside command plan, selected adapter, selected model, tracking mode, and stdout/stderr evidence
