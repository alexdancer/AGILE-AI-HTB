## MODIFIED Requirements

### Requirement: Budgets gate launches
The system SHALL evaluate remaining budget before launching Worker Sessions and block normal launch when the estimate exceeds remaining budget, using spend categories that distinguish control-plane, Worker execution, verification/overhead usage, and any external direct-OpenCode baseline evidence used for comparison demos.

#### Scenario: Estimate fits remaining budget
- **WHEN** a Task estimate is within remaining Worker execution budget and other Launch Guardrails pass
- **THEN** the Portal allows normal launch

#### Scenario: Estimate exceeds remaining budget
- **WHEN** a Task estimate exceeds remaining Worker execution budget before launch
- **THEN** the Portal blocks normal launch and offers an explicit budget override flow

#### Scenario: Control-plane spend shown separately
- **WHEN** AGILE-AI-HTB uses its own model for estimation, planning, recommendation, or reporting
- **THEN** the token ledger and budget UI classify that usage separately from Worker execution spend

#### Scenario: Direct OpenCode comparison baseline is outside harness budget
- **WHEN** an operator captures token usage from a direct OpenCode run for comparison
- **THEN** AGILE-AI-HTB treats that usage as external baseline evidence and does not subtract it from harness Worker launch budget unless a separate import feature explicitly does so

### Requirement: Budget enforcement uses Worker execution spend
Budget launch gating and budget alarm evals SHALL distinguish Worker execution spend from control-plane, task breakdown, adapter verification, reporting summary spend, and external direct-OpenCode baseline usage captured only for comparison.

#### Scenario: Control-plane estimation spend does not reduce Worker launch budget
- **WHEN** AGILE-AI-HTB uses its control-plane model to estimate or decompose a markdown task file
- **THEN** that usage is categorized outside Worker execution spend
- **AND** the remaining Worker launch budget is calculated from Worker execution usage only

#### Scenario: Comparison run uses a separately configured harness budget
- **WHEN** an operator runs the long OpenCode comparison task through AGILE-AI-HTB after collecting a direct OpenCode baseline
- **THEN** launch gating, overrides, alarms, and overrun evidence are based on the configured AGILE-AI-HTB Worker budget and recorded harness Worker execution usage, not the direct baseline budget or usage
