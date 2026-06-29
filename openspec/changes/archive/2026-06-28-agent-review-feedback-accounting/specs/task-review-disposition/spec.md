## MODIFIED Requirements

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
