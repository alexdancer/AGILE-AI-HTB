## MODIFIED Requirements

### Requirement: Token budget distinguishes enforcement from visibility
The Portal SHALL distinguish Worker budget enforcement from total tracked spend visibility. Agent Review SHALL count as control-plane orchestration/reporting spend in budget visibility while remaining separate from Worker execution actuals.

#### Scenario: Operator reviews budget scope
- **WHEN** the operator views token budget setup
- **THEN** the page explains that Worker launch budget enforcement is based on `worker_execution` spend
- **AND** the page explains that dashboard visibility may include control-plane, task breakdown, adapter verification, Agent Review/reporting, and Worker execution spend

#### Scenario: Dashboard summarizes budget usage by category
- **WHEN** tracked token usage exists for the current budget period
- **THEN** the budget summary shows `worker_execution` usage separately from orchestration/setup usage
- **AND** the summary shows total tracked usage for visibility

#### Scenario: Agent Review spend is categorized as orchestration
- **WHEN** Agent Review records token usage
- **THEN** the token ledger classifies that usage as control-plane orchestration/reporting spend
- **AND** total tracked budget visibility includes the Agent Review tokens
- **AND** task Worker execution actuals do not include the Agent Review tokens
