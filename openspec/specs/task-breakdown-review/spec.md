# task-breakdown-review Specification

## Purpose
Define how Proposed Task Breakdown review preserves decomposition intent, global source-contract context, and acceptance-verification work before accepted candidates become estimated AGILE Board Tasks.

## Requirements

### Requirement: Durable task breakdown review records
The system SHALL persist Task Breakdown Agent output as a durable Proposed Task Breakdown review record before creating AGILE Board Tasks from Markdown intake or oversized task intake.

#### Scenario: Markdown intake creates review record before tasks
- **WHEN** the operator submits Markdown upload or Markdown paste that requires Task Breakdown Agent interpretation
- **THEN** the system creates a durable Proposed Task Breakdown review record
- **AND** no AGILE Board Task is created until the operator accepts one or more candidates from that review

#### Scenario: Review record preserves breakdown evidence
- **WHEN** a Proposed Task Breakdown is created
- **THEN** the record preserves source metadata, candidate tasks, rejected/non-task items, constraints, verification criteria, decomposition confidence, Task Breakdown Model identity, and linked orchestration token/session evidence when available

### Requirement: Breakdown review page
The system SHALL provide a separate review page for Proposed Task Breakdowns rather than representing breakdown review as an AGILE Board column or Task state.

#### Scenario: Markdown intake redirects to review page
- **WHEN** Markdown intake successfully produces a Proposed Task Breakdown
- **THEN** the operator is redirected to a breakdown review page for that review record
- **AND** the AGILE Board remains limited to Task lifecycle columns

#### Scenario: Accepting review creates estimated tasks
- **WHEN** the operator accepts one or more candidate tasks from the breakdown review page
- **THEN** the system immediately sends the accepted candidates to Task Estimation
- **AND** creates Estimated AGILE Board Tasks for successful estimates
- **AND** returns the operator to the AGILE Board

### Requirement: Review shows candidates and non-task classifications
The breakdown review page SHALL show candidate vertical slices and explicitly show rejected or non-task source items with reasons.

#### Scenario: Constraint bullet is not a task
- **WHEN** the source contains a bullet such as “Do not add network dependencies.”
- **THEN** the breakdown review shows it as a constraint or rejected-as-task item with a reason
- **AND** the system does not estimate it as a standalone Task

#### Scenario: Verification bullet is not a task
- **WHEN** the source contains a bullet such as “Run pytest.”
- **THEN** the breakdown review shows it as verification criteria or rejected-as-task item with a reason
- **AND** the system does not estimate it as a standalone Task unless the operator explicitly edits it into an implementation candidate

### Requirement: Practical breakdown review editing
The breakdown review page SHALL support practical editing of accepted work without requiring a full planning editor.

#### Scenario: Operator edits candidates before acceptance
- **WHEN** the operator reviews a Proposed Task Breakdown
- **THEN** the operator can accept or reject candidates
- **AND** edit candidate titles or implementation prompts
- **AND** edit constraints and acceptance criteria text before submitting accepted candidates to Task Estimation

#### Scenario: Hard dependency enforcement is not required
- **WHEN** the Task Breakdown Agent suggests a recommended sequence
- **THEN** the system may preserve the sequence as metadata or creation order
- **AND** the first product slice does not require hard dependency blocking between created Tasks

### Requirement: Breakdown failure recovery
The system SHALL show an explicit breakdown-failed recovery state when the Task Breakdown Agent fails or returns invalid structure.

#### Scenario: Breakdown model unavailable
- **WHEN** the Task Breakdown Agent cannot complete because the model provider is unavailable, misconfigured, over budget, or returns invalid output
- **THEN** the system shows a breakdown-failed review/manual recovery screen
- **AND** offers retry, manual candidate creation, single manual candidate creation, or cancel actions
- **AND** does not silently fall back to deterministic Markdown splitting
- **AND** does not create an oversized Estimated Task from the whole source without operator action

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
