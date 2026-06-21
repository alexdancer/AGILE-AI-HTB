## MODIFIED Requirements

### Requirement: Running and Review reflect Worker Run state
The board SHALL use Running for active Worker Runs and Review for completed Worker Runs awaiting operator inspection. Review task cards SHALL show completed run evidence, expose review actions, and display the latest operator review prompt and Agent Review response when present.

#### Scenario: Active run appears Running
- **WHEN** a Worker Run is active for a task
- **THEN** the task appears in the Running column with active run metadata

#### Scenario: Completed run appears Review
- **WHEN** a Worker Run completes successfully with required evidence
- **THEN** the task appears in the Review column with a link or inline summary for run evidence
- **AND** the card shows Review actions for Agent Review, Mark Done, and Block
- **AND** the card provides an input for an optional operator review prompt or focus

#### Scenario: Review card displays saved prompt
- **WHEN** a Review task has a saved operator review prompt
- **THEN** the Review task card displays that prompt on the task card

#### Scenario: Review card displays Agent Review response
- **WHEN** a Review task has a completed Agent Review result
- **THEN** the Review task card displays the latest Agent Review summary or response
