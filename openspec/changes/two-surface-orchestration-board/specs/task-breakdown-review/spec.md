## MODIFIED Requirements

### Requirement: Acceptance Verification is ordinary Worker work
Acceptance Verification SHALL be an ordinary estimated Orchestration Board Task rather than a hidden control-plane check.

#### Scenario: Accepted Acceptance Verification becomes estimated Task
- **WHEN** the operator accepts an `acceptance_verification` candidate
- **THEN** the system sends it through Task Estimation
- **AND** creates an Estimated Orchestration Board Task when estimation succeeds
- **AND** the Task has its own Token Budget, Worker Run, and Review Disposition lifecycle

#### Scenario: Acceptance Verification verifies instead of rebuilding
- **WHEN** an Acceptance Verification Task is launched
- **THEN** the Worker prompt frames the work as verifying the combined artifact against the original source contract
- **AND** it does not ask the Worker to reimplement the whole source task as one oversized implementation Task

#### Scenario: Executable proof is preferred
- **WHEN** an Acceptance Verification Task runs
- **THEN** it uses the smallest executable proof available, such as tests, CLI smoke checks, API calls, artifact parsing, or invariant scans
- **AND** it produces human-readable findings
- **AND** if no executable proof is available, it labels the result manual verification only and explains the evidence gap

#### Scenario: Failed Acceptance Verification does not auto-create repair Tasks
- **WHEN** Acceptance Verification fails
- **THEN** the Task remains in Review with its human-readable findings
- **AND** the operator may record a structured Blocked Condition through normal Review Disposition without changing that Review lifecycle status
- **AND** the system does not automatically create repair Tasks from failure text
