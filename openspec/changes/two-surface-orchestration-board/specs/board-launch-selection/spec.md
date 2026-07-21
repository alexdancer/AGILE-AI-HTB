## MODIFIED Requirements

### Requirement: Blocked column is reserved for workflow blockers
The board SHALL represent workflow or dependency blockers, manual-estimate-required work, and hard safety guardrail states as a structured Blocked Condition on the task while preserving its canonical `Estimated`, `Running`, `Review`, or `Done` lifecycle status. Retryable Worker Run failures on otherwise launchable tasks SHALL remain relaunchable in `Estimated` with sanitized failure evidence. The board SHALL NOT expose or persist a `Blocked` lifecycle column.

#### Scenario: Operator sees dependency block separately from launch failure
- **WHEN** one task has workflow dependency metadata and another task has a recent Worker timeout
- **THEN** the dependency-blocked task remains in its canonical lifecycle position with a Blocked Condition reason badge
- **AND** the timed-out task appears in Estimated with a retry control while its full launch failure remains in lazy evidence
- **AND** neither task appears in a `Blocked` column

### Requirement: Board launch requires task-bound project root
The system SHALL require a connected project root before launching a normal Worker task from the project surfaces, and project-scoped launches SHALL require the task's project binding to match the selected project context.

#### Scenario: Launch uses selected project task root
- **WHEN** an authenticated operator launches an Estimated task from `/projects/{project_id}` or `/projects/{project_id}/floor`
- **AND** the task metadata is bound to `{project_id}`
- **AND** the bound project root matches a connected project record
- **THEN** the system SHALL pass that task-bound project root path as the Worker launch workdir
- **AND** the Worker Run evidence SHALL record the selected project id and project root used for launch

#### Scenario: Launch fails without connected project
- **WHEN** an authenticated operator launches an Estimated task from a compatibility or project entry point
- **AND** no connected project exists
- **THEN** the system SHALL reject the launch before starting any Worker Adapter process
- **AND** `/board` SHALL redirect the operator to `/projects` to connect a project

#### Scenario: Launch rejects task not bound to selected project
- **WHEN** an authenticated operator launches an Estimated task with selected `{project_id}` context
- **AND** the task metadata is missing a project binding or is bound to a different connected project id
- **THEN** the system SHALL reject the launch before starting any Worker Adapter process
- **AND** the task SHALL remain eligible for correction or recreation rather than launching against another repository
