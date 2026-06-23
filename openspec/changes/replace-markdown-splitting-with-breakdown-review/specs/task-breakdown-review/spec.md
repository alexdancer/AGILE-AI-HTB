## ADDED Requirements

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
