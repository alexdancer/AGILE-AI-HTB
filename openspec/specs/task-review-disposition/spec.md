# task-review-disposition

## Purpose

Define the operator-controlled Review-stage disposition flow for completed Worker execution so tasks can be reviewed, approved, blocked, or annotated while preserving Worker Run, session, token, and launch evidence.
## Requirements
### Requirement: Review tasks expose operator disposition actions
The system SHALL expose Review-stage actions for tasks awaiting operator inspection after completed Worker execution.

#### Scenario: Review task shows action panel
- **WHEN** a task is in Review
- **AND** the task is linked to completed Worker Run or completed session evidence
- **THEN** the board task card shows actions for Agent Review, Mark Done, and Block
- **AND** the task card provides an input for an optional operator review prompt or focus

### Requirement: Operator can mark reviewed task Done
The system SHALL let an operator approve a Review task and move it to Done without requiring Agent Review first.

#### Scenario: Operator marks Review task Done
- **WHEN** a task is in Review with completed Worker Run or session evidence
- **AND** the operator chooses Mark Done
- **THEN** the task moves to Done
- **AND** the system records operator review decision metadata
- **AND** existing Worker Run, session, token, actual token, and launch evidence remain linked to the task

#### Scenario: Done action rejects non-review task
- **WHEN** an operator requests Mark Done for a task that is not in Review
- **THEN** the system rejects the action without changing the task lifecycle status
- **AND** the response explains that only Review tasks can be marked Done from the review action

### Requirement: Operator can save review prompt
The system SHALL let an operator save a specific review prompt or focus while a task remains in Review.

#### Scenario: Operator saves review prompt
- **WHEN** a task is in Review
- **AND** the operator enters a review prompt or focus
- **THEN** the task remains in Review
- **AND** the prompt is stored on the task
- **AND** the Review task card displays the latest saved prompt

### Requirement: Agent Review uses control-plane model
The system SHALL perform Agent Review using the AGILE-AI-HTB control-plane/orchestrator model and SHALL NOT use the Worker Adapter model/auth as the review mechanism.

#### Scenario: Agent Review runs with task evidence
- **WHEN** a task is in Review
- **AND** the operator chooses Agent Review
- **THEN** the system builds a review request from task description, Worker Run evidence, session evidence, token evidence, launch metadata, and the latest operator review prompt when present
- **AND** the system sends that request through the configured control-plane/orchestrator model connection
- **AND** the task remains in Review

#### Scenario: Control-plane model unavailable for Agent Review
- **WHEN** an operator requests Agent Review
- **AND** no valid control-plane/orchestrator model connection is available
- **THEN** the task remains in Review
- **AND** the task records and displays a sanitized Agent Review failure reason
- **AND** Mark Done and Block remain available

### Requirement: Agent Review result is persisted and displayed
The system SHALL persist the latest Agent Review result on the task and display a concise response on the Review task card, including enough session/model/token evidence for the operator to see that the action completed.

#### Scenario: Agent Review completes
- **WHEN** Agent Review completes successfully
- **THEN** the task metadata records the review status, control-plane model, reviewed timestamp, summary, recommendation when available, findings when available, review session id, and Agent Review token totals when available
- **AND** the Review task card displays a visible Agent Review completion line with the recommendation or summary
- **AND** the Review task card shows or links the Agent Review session id and review token total when available
- **AND** the Agent Review result does not automatically move the task to Done, Estimated, or Blocked

#### Scenario: Agent Review fails visibly
- **WHEN** Agent Review fails due to model, parsing, or runtime error
- **THEN** the task remains in Review
- **AND** the task metadata records a sanitized Agent Review failure with review session id and model when available
- **AND** the Review task card displays a visible Agent Review failure line
- **AND** Mark Done and Block remain available

### Requirement: Operator can block reviewed task
The system SHALL let an operator move a Review task to Blocked with a human-readable reason.

#### Scenario: Operator blocks Review task
- **WHEN** a task is in Review
- **AND** the operator submits a non-empty block reason
- **THEN** the task moves to Blocked
- **AND** the task records blocked reason and review decision metadata
- **AND** existing Worker Run, session, token, and launch evidence remain linked to the task

#### Scenario: Block requires reason
- **WHEN** an operator requests Block for a Review task without a reason
- **THEN** the task remains in Review
- **AND** the board displays a validation error asking for a block reason

### Requirement: Auto Agent Review does not decide disposition
Automatic Agent Review SHALL be advisory evidence only and SHALL NOT replace operator Review Disposition.

#### Scenario: Auto review approval remains in Review
- **WHEN** Auto Agent Review completes with an approval or positive recommendation
- **THEN** the task SHALL remain in Review
- **AND** the operator SHALL still choose Mark Done before the task moves to Done

#### Scenario: Auto review findings remain in Review
- **WHEN** Auto Agent Review reports findings or a negative recommendation
- **THEN** the task SHALL remain in Review
- **AND** the operator SHALL still choose Block with a reason before the task moves to Blocked

#### Scenario: Auto review failure does not change task state
- **WHEN** Auto Agent Review fails due to control-plane model or parsing errors
- **THEN** the task SHALL remain in Review
- **AND** the Review card SHALL show review failure evidence without moving the task to Done or Blocked

### Requirement: Agent Review evidence links to the reviewed session report
The Review Disposition flow SHALL keep Agent Review evidence visible from the Review task card and from the Worker session report for the reviewed task.

#### Scenario: Review result is visible from task card and session report
- **WHEN** Agent Review completes for a Review task with a linked Worker session
- **THEN** the Review task card SHALL show the latest Agent Review status, recommendation or failure state, review token total when available, and review session link when available
- **AND** the Worker session report for that task SHALL show the same latest Agent Review result summary and review usage metadata

#### Scenario: Agent Review accounting stays orchestration-only
- **WHEN** Agent Review records token usage
- **THEN** that usage SHALL be categorized as control-plane reporting or orchestration spend
- **AND** it SHALL NOT be counted as Worker execution `actual_tokens` for the reviewed task
