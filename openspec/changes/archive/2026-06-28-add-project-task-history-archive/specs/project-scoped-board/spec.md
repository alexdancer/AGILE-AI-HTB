## ADDED Requirements

### Requirement: Project board preserves Done before archive
The project board SHALL keep newly completed tasks in the Done column until an operator archives them.

#### Scenario: Mark Done remains visible on board
- **WHEN** an operator marks a Review task Done for `/projects/{project_id}/board`
- **THEN** the task SHALL move to the Done column for that selected project
- **AND** the task SHALL NOT be archived automatically

### Requirement: Project board can archive Done cards
The project board SHALL provide archive actions for Done cards without changing task lifecycle status or deleting task evidence.

#### Scenario: Archive one Done card
- **WHEN** an authenticated operator chooses Archive on an unarchived Done card from `/projects/{project_id}/board`
- **THEN** the task SHALL record archive state in task metadata
- **AND** the task SHALL remain `Done`
- **AND** existing Worker Run, session, token, actual token, launch, and review evidence SHALL remain linked to the task
- **AND** the response SHALL return the operator to the selected project board or task history page

#### Scenario: Archive rejects non-Done task
- **WHEN** an authenticated operator requests Archive for a task that is not `Done`
- **THEN** the system SHALL reject the action without recording archive state
- **AND** the response SHALL explain that only Done tasks can be archived

### Requirement: Project board can archive all Done cards
The project board SHALL provide an Archive all Done action scoped to the selected connected project.

#### Scenario: Archive all Done affects only selected project Done tasks
- **WHEN** an authenticated operator chooses Archive all Done from `/projects/{project_id}/board`
- **THEN** the system SHALL archive every unarchived `Done` task bound to `{project_id}`
- **AND** it SHALL NOT archive Estimated, Running, Review, or Blocked tasks
- **AND** it SHALL NOT archive tasks bound to any other project
- **AND** already archived Done tasks SHALL remain archived without losing their original task evidence

### Requirement: Project board hides archived cards and links to history
The active project board SHALL hide archived tasks while keeping the task history/archive page discoverable.

#### Scenario: Archived task is hidden from board
- **WHEN** an authenticated operator opens `/projects/{project_id}/board`
- **AND** a selected-project task has archive state
- **THEN** the board SHALL NOT render that task in any active board column
- **AND** the task SHALL remain visible from the selected project's task history page

#### Scenario: Board links to task history
- **WHEN** an authenticated operator opens `/projects/{project_id}/board`
- **THEN** the board SHALL provide a link to `/projects/{project_id}/task-history`
- **AND** the link or nearby board summary SHALL make archived/history tasks discoverable without adding an Archived board column
