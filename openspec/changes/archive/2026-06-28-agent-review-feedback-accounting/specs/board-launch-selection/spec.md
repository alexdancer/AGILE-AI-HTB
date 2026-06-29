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
- **AND** the response includes a visible completion indicator without requiring the operator to expand raw details

#### Scenario: Agent Review action returns to visible result
- **WHEN** an operator submits Agent Review from a Review task card
- **AND** the Agent Review action completes or fails
- **THEN** the board response after redirect or refresh shows a visible Agent Review status line on that task card
- **AND** the line includes the review recommendation or failure state, review session id when available, and token total when available
