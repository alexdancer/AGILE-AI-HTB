# project-workspace Specification

## Purpose
Define the project workspace entry points that let authenticated operators connect local repositories, open project overviews, and navigate into project-scoped workflows while preserving access to global harness pages.
## Requirements
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
The project overview SHALL link to portal workflows in the context of the selected project when that workflow is project-scoped. Global settings and governance workflows SHALL remain reachable without duplicating their controls on the overview.

#### Scenario: Existing workflow links are available
- **WHEN** an authenticated operator opens a project overview
- **THEN** the overview SHALL link to the selected project's task board at `/projects/{project_id}/board`
- **AND** the overview SHALL link to the existing sessions list, Worker adapter settings, and project settings pages

### Requirement: Global harness pages remain available
The system SHALL keep existing global harness pages reachable after adding project workspace entry.

#### Scenario: Existing global dashboard remains reachable
- **WHEN** an authenticated operator navigates to `/dashboard`
- **THEN** the system SHALL render the existing global dashboard page

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

### Requirement: Project overview summarizes actionable repo state
The project overview SHALL summarize the selected repository's useful operator state before detailed repo profile data.

#### Scenario: Project overview shows next actions
- **WHEN** an authenticated operator opens `/projects/{project_id}`
- **THEN** the system SHALL show action cards or rows for the selected project's task board, Worker/setup readiness, running work, review-needed work, and relevant alarms or session evidence when available
- **AND** each action SHALL link to the existing workflow page that handles the action

#### Scenario: Project overview does not duplicate workflow forms
- **WHEN** the project overview shows setup, board, session, or alarm actions
- **THEN** it SHALL route the operator to existing workflow pages instead of duplicating launch, review, adapter verification, or alarm-resolution forms on the overview

### Requirement: Project overview keeps repo identity visible but secondary
The project overview SHALL keep repository identity and detected profile information available without making it the only useful content on the page.

#### Scenario: Repo profile remains visible after action summary
- **WHEN** an authenticated operator opens `/projects/{project_id}`
- **THEN** the page SHALL still show root path, branch, language/framework/package hints, test command, run command, and docs when available
- **AND** these details SHALL appear after or below the primary action/readiness summary

