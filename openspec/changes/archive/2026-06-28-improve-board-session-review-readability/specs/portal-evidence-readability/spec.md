## ADDED Requirements

### Requirement: Session report shows related Agent Review results
A Worker session report SHALL surface the latest Agent Review result from the task linked to that session when review metadata exists, before raw evidence sections.

#### Scenario: Worker session has completed Agent Review
- **WHEN** an operator opens a Worker session report
- **AND** a task linked to that session has completed Agent Review metadata
- **THEN** the report SHALL show an Agent Review results section with status, recommendation, summary, control-plane model, reviewed timestamp when available, review session link when available, and review token total when available
- **AND** the report SHALL keep detailed findings available in bounded or expandable evidence sections

#### Scenario: Worker session has failed Agent Review
- **WHEN** an operator opens a Worker session report
- **AND** a task linked to that session has failed Agent Review metadata
- **THEN** the report SHALL show the Agent Review failure status and sanitized failure evidence
- **AND** the report SHALL keep the Worker session evidence visible and unchanged

#### Scenario: Worker session has no Agent Review
- **WHEN** an operator opens a Worker session report
- **AND** no linked task has Agent Review metadata
- **THEN** the report SHALL not fabricate review results or zero review tokens

### Requirement: Review tokens remain separate from Worker execution totals
Session report review-result display SHALL show Agent Review token totals as control-plane/reporting evidence and SHALL NOT merge those tokens into Worker execution actuals.

#### Scenario: Review tokens are displayed separately
- **WHEN** a Worker session report shows related Agent Review metadata with token totals
- **THEN** the review token total SHALL be labeled as review/control-plane usage
- **AND** the Worker session token totals SHALL remain based on that Worker session's token log
- **AND** task actual Worker tokens SHALL remain unchanged
