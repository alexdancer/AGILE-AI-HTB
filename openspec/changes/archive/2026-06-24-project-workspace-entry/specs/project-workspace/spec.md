## ADDED Requirements

### Requirement: Portal lists project workspaces
The system SHALL provide a project workspace list page that shows connected local repositories and offers an open/connect repo form.

#### Scenario: Connected projects are listed
- **WHEN** an authenticated operator opens `/projects`
- **THEN** the system SHALL show connected projects ordered by most recently updated first
- **AND** each project entry SHALL link to its project overview

#### Scenario: No connected projects exist
- **WHEN** an authenticated operator opens `/projects` with no connected projects
- **THEN** the system SHALL show an open/connect repo form

### Requirement: Portal opens a project overview
The system SHALL provide a project overview page for each connected project using existing project profile and capability data.

#### Scenario: Project overview renders repo identity
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an existing connected project
- **THEN** the system SHALL show the project name, root path, detected branch, language hints, framework hints, package manager hints, test command, run command, and relevant docs when available

#### Scenario: Project overview renders launch readiness
- **WHEN** an authenticated operator opens `/projects/{project_id}`
- **THEN** the system SHALL show the project's current Local Runner capability state and any missing launch capability reasons

#### Scenario: Missing project returns not found
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an unknown project id
- **THEN** the system SHALL return a not found response

### Requirement: Login enters the most recent project workspace
The system SHALL route authenticated operators into a project workspace by default when a connected project exists.

#### Scenario: Login redirects to most recent project
- **WHEN** an operator successfully logs in and at least one connected project exists
- **THEN** the system SHALL redirect to `/projects/{project_id}` for the most recently updated connected project

#### Scenario: Login redirects to project list without projects
- **WHEN** an operator successfully logs in and no connected projects exist
- **THEN** the system SHALL redirect to `/projects`

### Requirement: Project overview links to existing workflows
The project overview SHALL link to existing portal workflows instead of duplicating board, session, Worker adapter, or project settings controls.

#### Scenario: Existing workflow links are available
- **WHEN** an authenticated operator opens a project overview
- **THEN** the overview SHALL link to the existing task board, sessions list, Worker adapter settings, and project settings pages

### Requirement: Global harness pages remain available
The system SHALL keep existing global harness pages reachable after adding project workspace entry.

#### Scenario: Existing global dashboard remains reachable
- **WHEN** an authenticated operator navigates to `/dashboard`
- **THEN** the system SHALL render the existing global dashboard page
