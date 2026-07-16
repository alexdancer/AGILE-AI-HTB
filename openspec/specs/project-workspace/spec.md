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
The system SHALL provide a React-owned project overview surface for each connected project at the canonical `/projects/{project_id}` URL, using the existing project profile, capability, archive, and workspace-summary data. When the React build is missing or partial, that URL SHALL return the missing-build recovery response; no server-rendered project overview SHALL remain.

#### Scenario: Project overview renders repo identity
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an existing connected project while the complete React build is available
- **THEN** React SHALL show the project name, root path, detected branch, language hints, framework hints, package manager hints, test command, run command, and relevant docs when available
- **AND** missing scalar values and collections SHALL render typed concise unavailable/empty states rather than `undefined` or raw JSON

#### Scenario: Missing or partial build returns the recovery response
- **WHEN** an authenticated operator opens `/projects/{project_id}` while the React build is missing or partial
- **THEN** the system SHALL return the missing-build recovery response at the same canonical URL
- **AND** it SHALL NOT render a server-rendered project overview, which no longer exists

#### Scenario: Project overview renders launch readiness
- **WHEN** an authenticated operator opens the project overview
- **THEN** the system SHALL show the project's current Local Runner capability state and any missing launch capability reasons

#### Scenario: Missing project returns not found
- **WHEN** an authenticated operator opens the project overview for an unknown project id
- **THEN** the backend SHALL return not found
- **AND** React SHALL render a bounded error state rather than a partial project surface
### Requirement: Login enters the most recent project workspace
The system SHALL route authenticated operators into a project workspace by default when a connected project exists.

#### Scenario: Login redirects to most recent project
- **WHEN** an operator successfully logs in and at least one connected project exists
- **THEN** the system SHALL redirect to `/projects/{project_id}` for the most recently updated connected project

#### Scenario: Login redirects to project list without projects
- **WHEN** an operator successfully logs in and no connected projects exist
- **THEN** the system SHALL redirect to `/projects`

### Requirement: Project overview links to existing workflows
The project overview SHALL link to Portal workflows in the context of the selected project when that workflow is project-scoped. The migrated React overview SHALL keep the migrated board in-shell; global and non-migrated settings/governance workflows SHALL remain reachable without duplicating their controls on the overview.

#### Scenario: Server-rendered workflow links remain available
- **WHEN** an authenticated operator opens `/projects/{project_id}`
- **THEN** the overview SHALL link to the selected project's task board at `/projects/{project_id}/board`
- **AND** the overview SHALL link to the existing sessions list, Worker adapter settings, and project settings pages

#### Scenario: React workflow links follow route ownership
- **WHEN** an authenticated operator opens `/app/projects/{project_id}` for an active project
- **THEN** the overview SHALL link in-shell to `/app/projects/{project_id}/board`
- **AND** board-targeting attention actions SHALL use that same React board route
- **AND** task history, Sessions, Worker setup, and Project settings SHALL remain ordinary full-page links to their existing Portal routes
- **AND** the overview SHALL not duplicate those workflow forms

#### Scenario: Archived React overview suppresses active board entry
- **WHEN** an authenticated operator opens `/app/projects/{project_id}` for an archived project
- **THEN** the overview SHALL retain task history and session/evidence links
- **AND** it SHALL show Restore instead of active board or launch entry points

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
Both project overview surfaces SHALL summarize the selected repository's useful operator state before detailed repo profile data. React SHALL render this state from the bounded FastAPI workspace projection and SHALL not infer readiness or lifecycle state locally.

#### Scenario: Project overview shows next actions
- **WHEN** an authenticated operator opens either project overview surface
- **THEN** the system SHALL show action cards or rows for the selected project's task board, Worker/setup readiness, running work, review-needed work, and relevant alarms or session evidence when available
- **AND** each action SHALL link to the workflow that handles the action

#### Scenario: React overview uses authoritative refreshed state
- **WHEN** project capability, launch readiness, task counts, attention state, or archive state changes
- **THEN** React SHALL show values from the refreshed FastAPI projection
- **AND** it SHALL not optimistically infer those values

#### Scenario: Project overview does not duplicate workflow forms
- **WHEN** either project overview shows setup, board, session, or alarm actions
- **THEN** it SHALL route the operator to existing workflow pages instead of duplicating launch, review, adapter verification, or alarm-resolution forms on the overview

### Requirement: Project overview keeps repo identity visible but secondary
Both project overview surfaces SHALL keep repository identity and detected profile information available without making it the only useful content on the page.

#### Scenario: Repo profile remains visible after action summary
- **WHEN** an authenticated operator opens either `/projects/{project_id}` or `/app/projects/{project_id}`
- **THEN** the page SHALL still show root path, branch, language/framework/package hints, test command, run command, and docs when available
- **AND** these details SHALL appear after or below the primary action/readiness summary

#### Scenario: React repo profile remains bounded
- **WHEN** profile strings or collections are long or malformed
- **THEN** React SHALL render only the sanitized, truncated, typed profile projection defined by the React Portal shell contract
- **AND** it SHALL not render raw internal project metadata

### Requirement: No-auth local entry uses project workspace landing
The project workspace entry flow SHALL route no-auth local operators to the same project landing used after successful login.

#### Scenario: No-auth root redirects to most recent project
- **WHEN** portal auth is not required
- **AND** at least one connected project exists
- **THEN** `GET /` SHALL redirect to `/projects/{project_id}` for the most recently updated connected project

#### Scenario: No-auth root redirects to project list without projects
- **WHEN** portal auth is not required
- **AND** no connected projects exist
- **THEN** `GET /` SHALL redirect to `/projects`

