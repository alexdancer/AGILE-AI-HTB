## ADDED Requirements

### Requirement: Sidebar provides project repository switching
The system SHALL show connected project repositories in the portal sidebar as first-class project navigation.

#### Scenario: Connected projects are visible in sidebar
- **WHEN** an authenticated operator opens any portal page after connecting one or more projects
- **THEN** the sidebar SHALL list the connected project repositories by name
- **AND** each listed project SHALL link to `/projects/{project_id}`

#### Scenario: Active project is highlighted
- **WHEN** an authenticated operator opens `/projects/{project_id}` or `/projects/{project_id}/board`
- **THEN** the sidebar SHALL visually mark that project as active

#### Scenario: Project board remains scoped from selected project
- **WHEN** an authenticated operator opens the active project's board navigation from the project workspace
- **THEN** the system SHALL route to `/projects/{project_id}/board`

### Requirement: Project selection copy is operator-facing
The system SHALL present repository selection using project workspace language instead of making settings terminology primary.

#### Scenario: Project navigation uses workspace language
- **WHEN** an authenticated operator views project navigation or repo-opening controls
- **THEN** labels SHALL use terms such as `Projects`, `Open local repo`, `Open project`, or `Switch project`
- **AND** `Connected project` SHALL NOT be the primary label for the project selection experience
