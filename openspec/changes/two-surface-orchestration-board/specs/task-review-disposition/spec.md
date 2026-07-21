## MODIFIED Requirements

### Requirement: Review tasks expose operator disposition actions
The system SHALL expose Review-stage actions for tasks awaiting operator inspection after completed Worker execution, and SHALL present those actions inside the Evidence Drawer alongside the evidence they act on, so evidence and decision appear on one screen while the review queue stays visible.

#### Scenario: Review task shows action panel in the Evidence Drawer
- **WHEN** a task is in Review
- **AND** the task is linked to completed Worker Run or completed session evidence
- **AND** the operator opens the Evidence Drawer for that task
- **THEN** the drawer SHALL show actions for Agent Review, Mark Done, and Block
- **AND** the drawer SHALL provide an input for an optional operator review prompt or focus

#### Scenario: Review queue stays visible while deciding
- **WHEN** the Evidence Drawer is open for a Review task on the Execution Floor
- **THEN** the review queue SHALL remain visible beside the drawer
- **AND** taking a disposition action SHALL not require navigating away from the Floor

### Requirement: Operator can block reviewed task
The system SHALL let an operator record a structured Blocked Condition on a Review task with a human-readable reason while preserving the task's Review lifecycle status and linked evidence.

#### Scenario: Operator blocks Review task
- **WHEN** a task is in Review
- **AND** the operator submits a non-empty block reason
- **THEN** the task remains in Review
- **AND** the task records a Blocked Condition containing the sanitized reason, review origin, and timestamp
- **AND** existing Worker Run, session, token, and launch evidence remain linked to the task

#### Scenario: Block requires reason
- **WHEN** an operator requests Block for a Review task without a reason
- **THEN** the task remains in Review
- **AND** the board displays a validation error asking for a block reason

#### Scenario: Mark Done clears a resolved review Blocked Condition
- **WHEN** an operator marks a Review task Done after resolving its Blocked Condition
- **THEN** the task moves to Done
- **AND** the resolved Blocked Condition and legacy blocked-reason markers are removed

### Requirement: Auto Agent Review does not decide disposition
Automatic Agent Review SHALL be advisory evidence only and SHALL NOT replace operator Review Disposition.

#### Scenario: Auto review approval remains in Review
- **WHEN** Auto Agent Review completes with an approval or positive recommendation
- **THEN** the task SHALL remain in Review
- **AND** the operator SHALL still choose Mark Done before the task moves to Done

#### Scenario: Auto review findings remain in Review
- **WHEN** Auto Agent Review reports findings or a negative recommendation
- **THEN** the task SHALL remain in Review
- **AND** the operator SHALL still choose Block with a reason before a Blocked Condition is recorded

#### Scenario: Auto review failure does not change task state
- **WHEN** Auto Agent Review fails due to control-plane model or parsing errors
- **THEN** the task SHALL remain in Review
- **AND** the Review card SHALL show review failure evidence without moving the task to Done or recording a Blocked Condition
