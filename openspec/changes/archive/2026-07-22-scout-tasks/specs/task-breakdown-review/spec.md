## MODIFIED Requirements

### Requirement: Candidate kind is explicit
The system SHALL classify every Proposed Task Breakdown candidate as `implementation`, `scout`, or `acceptance_verification`.

#### Scenario: Proposed candidate includes kind
- **WHEN** the Task Breakdown Agent returns a Proposed Task Breakdown with candidate Tasks
- **THEN** each candidate includes a candidate kind
- **AND** the candidate kind is `implementation`, `scout`, or `acceptance_verification`

#### Scenario: Investigation intent does not depend on prose
- **WHEN** a candidate is intended to answer a bounded repository question without modifying the project
- **THEN** the candidate kind is `scout`
- **AND** the system does not infer that intent from the candidate title, prompt text, or read-only flag alone

#### Scenario: Verification intent does not depend on prose
- **WHEN** a candidate is intended to verify the integrated artifact against the original source contract
- **THEN** the candidate kind is `acceptance_verification`
- **AND** the system does not infer that intent from the candidate title or prompt text alone

#### Scenario: Operator edits candidate kind
- **WHEN** the operator reviews candidate Tasks on the Task Breakdown Review page
- **THEN** the operator can edit candidate kind
- **AND** the only available values are `implementation`, `scout`, and `acceptance_verification`

### Requirement: Candidates classify execution mode
Every Proposed Task Breakdown candidate SHALL classify whether it is autonomous or human-in-the-loop before it becomes an Orchestration Board Task.

#### Scenario: AFK candidate is independently executable
- **WHEN** a candidate can be implemented and verified by a Worker without waiting for operator decisions, credentials, external approvals, or manual product judgment during execution
- **THEN** the candidate execution mode SHALL be `AFK`
- **AND** the candidate SHALL include a runnable or inspectable verification proof where feasible

#### Scenario: HITL candidate names human dependency
- **WHEN** a candidate requires operator choice, manual QA, external approval, credentials, deployment permission, or stakeholder review before completion
- **THEN** the candidate execution mode SHALL be `HITL`
- **AND** the candidate SHALL include the reason human input is required

#### Scenario: Execution mode is separate from candidate kind
- **WHEN** a candidate is classified for Task Breakdown Review
- **THEN** `execution_mode` SHALL NOT replace candidate `kind`
- **AND** candidate `kind` SHALL continue to distinguish `implementation`, `scout`, and `acceptance_verification`

## ADDED Requirements

### Requirement: Task Breakdown Agent proposes Scouts only for bounded uncertainty
The Task Breakdown Agent SHALL propose a Scout only when a bounded unanswered repository question materially prevents an honest implementation estimate or independently executable slice. It SHALL NOT use Scout as a generic research, setup, or speculative pre-work category.

#### Scenario: Bounded repository uncertainty needs investigation
- **WHEN** source intake requires repository facts that bounded Repo Context cannot establish
- **AND** those facts materially affect scope, estimate, or implementation boundaries
- **THEN** the Task Breakdown Agent MAY propose a `scout` candidate
- **AND** the candidate identifies the question, inspection boundary, expected findings, and proof path

#### Scenario: Implementation-time inspection is sufficient
- **WHEN** an implementation Worker can inspect the relevant files as an ordinary part of a narrow executable slice
- **THEN** the Task Breakdown Agent keeps that inspection inside the `implementation` candidate
- **AND** it does not add a separate Scout

#### Scenario: Generic research is rejected
- **WHEN** proposed Scout work is speculative, unbounded, duplicates existing context, or has no concrete findings artifact
- **THEN** the Task Slicing Policy rejects it as a standalone candidate with a reason

### Requirement: Accepted Scout preserves bounded investigation context
An accepted Scout candidate SHALL preserve enough context to answer its investigation question while remaining read-only and smaller than implementation work.

#### Scenario: Operator accepts Scout candidate
- **WHEN** the operator accepts a `scout` candidate from Task Breakdown Review
- **THEN** the created Task stores canonical `task_kind: scout`
- **AND** its estimation and Worker-facing text includes the bounded question, inspection boundary, relevant constraints, expected findings, and proof
- **AND** it omits unrelated sibling implementation details and unnecessary raw source prose

#### Scenario: Scout candidate links to target task
- **WHEN** a proposed Scout exists to de-risk a specific Task already known to the Harness
- **THEN** acceptance preserves that target Task relationship in bounded metadata
- **AND** accepting the Scout does not alter the target Task's estimate or lifecycle
