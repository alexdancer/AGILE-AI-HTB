## MODIFIED Requirements

### Requirement: Worker launch model selection
The system SHALL launch Worker Sessions with a model selected from the verified adapter's operator-approved allowed model subset. A model that is discovered but not allowed SHALL NOT be launchable from the normal AGILE Board.

#### Scenario: User selects allowed Worker model
- **WHEN** the User launches a task with a model allowed for the selected verified Worker Adapter
- **THEN** the Local Runner passes that model to the Worker Harness launch command and records it on the Worker session

#### Scenario: Selected model is unavailable
- **WHEN** the selected model is not in the selected adapter's allowed model subset
- **THEN** the system blocks launch and shows the model compatibility reason

#### Scenario: Discovered but disallowed model is rejected
- **WHEN** a Worker Adapter has discovered model `opencode/experimental-large`
- **AND** the operator has not included it in the allowed model subset
- **AND** a launch request names `opencode/experimental-large`
- **THEN** the system rejects the launch before starting any Worker Adapter process
