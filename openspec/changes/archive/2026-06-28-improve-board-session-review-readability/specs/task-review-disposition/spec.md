## ADDED Requirements

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
