## ADDED Requirements

### Requirement: Candidate kind is explicit
The system SHALL classify every Proposed Task Breakdown candidate as either `implementation` or `acceptance_verification`.

#### Scenario: Proposed candidate includes kind
- **WHEN** the Task Breakdown Agent returns a Proposed Task Breakdown with candidate Tasks
- **THEN** each candidate includes a candidate kind
- **AND** the candidate kind is either `implementation` or `acceptance_verification`

#### Scenario: Verification intent does not depend on prose
- **WHEN** a candidate is intended to verify the integrated artifact against the original source contract
- **THEN** the candidate kind is `acceptance_verification`
- **AND** the system does not infer that intent from the candidate title or prompt text alone

#### Scenario: Operator edits candidate kind
- **WHEN** the operator reviews candidate Tasks on the Task Breakdown Review page
- **THEN** the operator can edit candidate kind
- **AND** the only available values are `implementation` and `acceptance_verification`

### Requirement: Global contract summary is preserved
The system SHALL preserve one editable global contract summary for each Proposed Task Breakdown and carry it into accepted implementation Tasks.

#### Scenario: Breakdown includes global contract summary
- **WHEN** the Task Breakdown Agent creates a Proposed Task Breakdown
- **THEN** the breakdown includes a global contract summary describing what the accepted slices must collectively satisfy

#### Scenario: Operator edits global contract summary
- **WHEN** the operator reviews a Proposed Task Breakdown
- **THEN** the review page displays the global contract summary
- **AND** the operator can edit the global contract summary before accepting candidates

#### Scenario: Implementation slices inherit global contract summary
- **WHEN** the operator accepts an `implementation` candidate
- **THEN** the accepted Task sent to Task Estimation includes the global contract summary
- **AND** it includes relevant global or candidate-scoped constraints

#### Scenario: Acceptance Verification carries full source contract
- **WHEN** the operator accepts an `acceptance_verification` candidate
- **THEN** the accepted Task sent to Task Estimation includes the global contract summary
- **AND** it includes the full original source contract needed to verify the combined artifact

### Requirement: Acceptance Verification is proposed for integrated artifacts
The Task Breakdown Agent SHALL auto-propose an Acceptance Verification candidate for multi-slice breakdowns that produce one integrated artifact.

#### Scenario: Integrated artifact receives final verification candidate
- **WHEN** source work is split into multiple implementation candidates for one integrated artifact such as a CLI, app, API, demo, or report
- **THEN** the Proposed Task Breakdown includes an `acceptance_verification` candidate
- **AND** that candidate is recommended last

#### Scenario: Independent slices may reject final verification
- **WHEN** the Task Breakdown Review page shows an `acceptance_verification` candidate
- **THEN** the operator can reject that candidate before creating board Tasks
- **AND** rejecting it does not prevent accepting other implementation candidates

#### Scenario: Launch order is not hard-blocked
- **WHEN** accepted candidates become Estimated AGILE Board Tasks
- **THEN** Acceptance Verification sequence is preserved as metadata or creation order
- **AND** the first implementation does not require hard dependency blocking between created Tasks

### Requirement: Acceptance Verification is ordinary Worker work
Acceptance Verification SHALL be an ordinary estimated AGILE Board Task rather than a hidden control-plane check.

#### Scenario: Accepted Acceptance Verification becomes estimated Task
- **WHEN** the operator accepts an `acceptance_verification` candidate
- **THEN** the system sends it through Task Estimation
- **AND** creates an Estimated AGILE Board Task when estimation succeeds
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
- **THEN** the Task moves to Blocked with findings
- **AND** the system does not automatically create repair Tasks from failure text
