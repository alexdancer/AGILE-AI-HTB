## ADDED Requirements

### Requirement: Setup pages show the next missing setup action
Setup and Worker Adapter pages SHALL identify the next missing action needed to make the Portal launch-ready.

#### Scenario: Worker setup highlights next missing action
- **WHEN** an authenticated operator opens Worker Adapter setup and the active adapter is not launchable
- **THEN** the page SHALL show the next missing setup action such as select default adapter, discover models, allow models, verify tracking, or connect/open a project when that context is missing
- **AND** the page SHALL link or focus the existing control that completes that action

#### Scenario: Launch-ready setup shows board action
- **WHEN** required setup is complete for launching governed tasks
- **THEN** the setup surface SHALL show a launch-ready state and link to the appropriate project board or project selection surface

### Requirement: Advanced diagnostics are secondary
Worker/setup diagnostics SHALL remain available without overwhelming the first setup path.

#### Scenario: Diagnostic detail remains available
- **WHEN** adapter diagnostics, verification evidence, tracking details, or model discovery evidence exist
- **THEN** the page SHALL keep that evidence available behind native disclosure or an advanced details section

#### Scenario: Primary setup path is readable
- **WHEN** an operator is completing setup for the first time
- **THEN** advanced diagnostics SHALL NOT be required reading before the next missing action is visible
