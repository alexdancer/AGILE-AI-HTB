## MODIFIED Requirements

### Requirement: Global board route is safe compatibility entry
The system SHALL avoid presenting `/board` as an ambiguous launch surface when active, non-archived project workspaces exist.

#### Scenario: Global board redirects to recent active project board
- **WHEN** an authenticated operator opens `/board`
- **AND** at least one non-archived connected project exists
- **THEN** the system SHALL redirect to `/projects/{project_id}/board` for the most recently updated non-archived connected project
- **AND** archived connected projects SHALL NOT be selected for this default redirect

#### Scenario: Global board redirects to projects without active connected projects
- **WHEN** an authenticated operator opens `/board`
- **AND** no non-archived connected projects exist
- **THEN** the system SHALL redirect to `/projects`
