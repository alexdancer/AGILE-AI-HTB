## ADDED Requirements

### Requirement: Alarm evals cover budget zone transitions
The system SHALL include behavior-level alarm evals that exercise yellow/red budget zone transitions using synthetic Worker execution usage.

#### Scenario: Yellow and red zones produce expected alarms
- **WHEN** synthetic Worker execution usage crosses yellow and red budget thresholds
- **THEN** the alarm detector emits the expected alarm types and severities
- **AND** each alarm context includes the budget zone and usage evidence needed for debugging

### Requirement: Alarm evals cover cap boundaries
The system SHALL include behavior-level alarm evals for daily cap and session cap boundaries.

#### Scenario: Daily and session caps produce expected alarms
- **WHEN** synthetic Worker execution usage exceeds the daily cap and session cap
- **THEN** the system records the expected cap alarms
- **AND** the alarms are associated with the relevant session when applicable

### Requirement: Alarm evals cover visibility and deduplication
The system SHALL verify that generated budget alarms remain visible in operator surfaces and are not duplicated by repeated detection over the same evidence.

#### Scenario: Alarm visible in dashboard and session report once
- **WHEN** a budget alarm has been generated for a Worker session
- **AND** the dashboard and session report are loaded
- **THEN** both surfaces show the alarm
- **AND** repeated alarm detection does not create duplicate visible alarm entries for the same condition
