## MODIFIED Requirements

### Requirement: Project board can archive Done cards
The project board SHALL provide archive actions for Done and Blocked cards without changing task lifecycle status or deleting task evidence.

#### Scenario: Archive one Done card
- **WHEN** an authenticated operator chooses Archive on an unarchived Done card from `/projects/{project_id}/board`
- **THEN** the task SHALL record archive state in task metadata
- **AND** the task SHALL remain `Done`
- **AND** existing Worker Run, session, token, actual token, launch, and review evidence SHALL remain linked to the task
- **AND** the response SHALL return the operator to the selected project board or task history page

#### Scenario: Archive one Blocked card
- **WHEN** an authenticated operator chooses Archive on an unarchived Blocked card from `/projects/{project_id}/board`
- **THEN** the task SHALL record archive state in task metadata
- **AND** the task SHALL remain `Blocked`
- **AND** blocked reason, manual-estimate, launch, Worker Run, session, token, and review evidence present on the task SHALL remain linked to the task
- **AND** the archived task SHALL be hidden from the selected project's active board columns
- **AND** the response SHALL return the operator to the selected project board or task history page

#### Scenario: Archive rejects active non-archivable task
- **WHEN** an authenticated operator requests Archive for a task whose status is not `Done` or `Blocked`
- **THEN** the system SHALL reject the action without recording archive state
- **AND** the response SHALL explain that only Done or Blocked tasks can be archived
