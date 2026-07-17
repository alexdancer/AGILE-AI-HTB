## MODIFIED Requirements

### Requirement: Portal opens a project overview
The system SHALL provide server-rendered and React-owned project overview surfaces for each connected project using the same existing project profile, capability, archive, and workspace-summary data. The Jinja overview SHALL remain available as fallback while the React overview preserves the same operator-facing contract.

#### Scenario: Server-rendered project overview renders repo identity
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an existing connected project
- **THEN** the system SHALL show the project name, root path, detected branch, language hints, framework hints, package manager hints, test command, run command, and relevant docs when available

#### Scenario: React project overview renders repo identity
- **WHEN** an authenticated operator opens `/app/projects/{project_id}` for an existing connected project
- **THEN** React SHALL show the same project name, root path, detected branch, language hints, framework hints, package manager hints, test command, run command, and relevant docs when available
- **AND** missing scalar values and collections SHALL render typed concise unavailable/empty states rather than `undefined` or raw JSON

#### Scenario: Project overview renders launch readiness
- **WHEN** an authenticated operator opens either project overview surface
- **THEN** the system SHALL show the project's current Local Runner capability state and any missing launch capability reasons

#### Scenario: Missing project returns not found
- **WHEN** an authenticated operator opens either project overview surface for an unknown project id
- **THEN** the backend SHALL return not found
- **AND** React SHALL render a bounded error state rather than a partial project surface

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