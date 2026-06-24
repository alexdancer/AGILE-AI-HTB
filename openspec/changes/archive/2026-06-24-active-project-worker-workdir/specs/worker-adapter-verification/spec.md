## ADDED Requirements

### Requirement: Worker Adapter setup does not own project workdir
The system SHALL keep normal task project root selection in the project workspace flow, not in per-adapter Worker settings.

#### Scenario: Worker settings separates adapter setup from project workspace
- **WHEN** an authenticated operator opens Worker Adapter settings
- **THEN** the system SHALL present Worker Adapter setup as CLI/auth/model/tracking configuration
- **AND** the system SHALL NOT require a per-adapter project workdir to make a verified adapter launchable for normal board tasks

#### Scenario: Adapter verification remains project independent
- **WHEN** an operator verifies a Worker Adapter
- **THEN** verification SHALL prove the adapter's CLI path and tracking mode evidence
- **AND** verification SHALL NOT be treated as selecting or configuring the project workspace for normal launches

### Requirement: Launch readiness combines adapter tracking and project availability
The system SHALL treat normal Worker launch readiness as the combination of a launchable Worker Adapter and an available connected project root.

#### Scenario: Verified adapter without project is not enough to launch
- **WHEN** a Worker Adapter has budget-authoritative verification
- **AND** no connected project root is available
- **THEN** the adapter remains verified
- **BUT** normal board launch SHALL be rejected until a project is opened

#### Scenario: Project without verified adapter is not enough to launch
- **WHEN** a connected project exists
- **AND** the selected Worker Adapter is unverified or observed-only
- **THEN** normal board launch SHALL remain blocked by Worker Adapter guardrails
