## ADDED Requirements

### Requirement: Run automation remains bound to selected project board
Project board run automation SHALL launch only tasks that are bound to the selected connected project.

#### Scenario: Queue only sees selected project tasks
- **WHEN** an operator starts run automation from `/projects/{project_id}/board`
- **THEN** the automation SHALL consider only tasks whose metadata is bound to `{project_id}`

#### Scenario: Queue does not fall back to another project
- **WHEN** no eligible tasks exist for the selected project
- **AND** another connected project has eligible tasks
- **THEN** the selected project's run automation SHALL NOT launch tasks from the other project
- **AND** it SHALL report that no eligible tasks exist for the selected project

#### Scenario: Project mismatch blocks automation launch
- **WHEN** run automation attempts to launch a task whose bound project id differs from the selected project id
- **THEN** the launch SHALL be rejected before starting any Worker Adapter process
