## MODIFIED Requirements

### Requirement: Archived project direct access preserves audit history
The system SHALL keep archived project Pipeline and Execution Floor URLs accessible for audit and restore while making archived state obvious and avoiding normal launch encouragement. Legacy board aliases SHALL continue to hand off to the archived Pipeline.

#### Scenario: Open archived project Pipeline directly
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an archived connected project
- **THEN** the Pipeline SHALL render the selected project with an archived banner
- **AND** it SHALL provide a Restore project action
- **AND** task history and session evidence links SHALL remain available

#### Scenario: Archived Execution Floor access is restore-first
- **WHEN** an authenticated operator opens `/projects/{project_id}/floor` for an archived connected project
- **THEN** the response SHALL clearly indicate that the project is archived
- **AND** it SHALL provide a route back to the Pipeline Restore action
- **AND** the system SHALL NOT launch new Worker work for the archived project unless it is restored first

#### Scenario: Archived legacy board access hands off to Pipeline
- **WHEN** an authenticated operator opens `/projects/{project_id}/board` for an archived connected project
- **THEN** the response SHALL redirect to `/projects/{project_id}`
- **AND** retained audit and Restore access SHALL not depend on a retired board view
