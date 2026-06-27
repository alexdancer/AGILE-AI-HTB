## MODIFIED Requirements

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
