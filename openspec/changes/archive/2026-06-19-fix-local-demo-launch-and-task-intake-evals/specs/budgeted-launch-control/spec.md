## ADDED Requirements

### Requirement: Budget alarms are behaviorally evaluated
The system SHALL include behavioral eval coverage for budget alarms that verifies alarm generation, deduplication, dashboard visibility, and session report visibility across budget zone and cap-boundary scenarios.

#### Scenario: Budget zone alarm appears in operator surfaces
- **WHEN** Worker execution usage crosses a configured budget zone threshold
- **THEN** the system records the expected budget alarm
- **AND** the dashboard exposes the alarm
- **AND** the session report exposes the alarm

#### Scenario: Cap boundary alarm is not duplicated
- **WHEN** a Worker session crosses a daily or session cap boundary and the alarm detector runs more than once for the same evidence
- **THEN** the system stores a single actionable alarm for that cap boundary

### Requirement: Budget enforcement uses Worker execution spend
Budget launch gating and budget alarm evals SHALL distinguish Worker execution spend from control-plane, task breakdown, adapter verification, and reporting summary spend.

#### Scenario: Control-plane estimation spend does not reduce Worker launch budget
- **WHEN** AGILE-AI-HTB uses its control-plane model to estimate or decompose a markdown task file
- **THEN** that usage is categorized outside Worker execution spend
- **AND** the remaining Worker launch budget is calculated from Worker execution usage only
