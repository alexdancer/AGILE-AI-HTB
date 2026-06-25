## MODIFIED Requirements

### Requirement: Board launch requires task-bound project root
The system SHALL require a connected project root before launching a normal Worker task from the board, and project-scoped board launches SHALL require the task's project binding to match the selected project board context.

#### Scenario: Launch uses selected project task root
- **WHEN** an authenticated operator launches an Estimated task from `/projects/{project_id}/board`
- **AND** the task metadata is bound to `{project_id}`
- **AND** the bound project root matches a connected project record
- **THEN** the system SHALL pass that task-bound project root path as the Worker launch workdir
- **AND** the Worker Run evidence SHALL record the selected project id and project root used for the launch

#### Scenario: Launch fails without connected project
- **WHEN** an authenticated operator launches an Estimated task from a board entry point
- **AND** no connected project exists
- **THEN** the system SHALL reject the launch before starting any Worker Adapter process
- **AND** `/board` SHALL redirect the operator to `/projects` to connect a project

#### Scenario: Launch rejects task not bound to selected project
- **WHEN** an authenticated operator launches an Estimated task from `/projects/{project_id}/board`
- **AND** the task metadata is missing a project binding or is bound to a different connected project id
- **THEN** the system SHALL reject the launch before starting any Worker Adapter process
- **AND** the task SHALL remain eligible for correction or recreation rather than launching against another repository
