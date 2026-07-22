## MODIFIED Requirements

### Requirement: Portal opens a project overview
The system SHALL provide a React-owned Pipeline Surface for each connected project at the canonical `/projects/{project_id}` URL, which serves as the project home and absorbs the project overview: repo identity and launch readiness are shown as the surface header, above task intake and the Estimated tasks. The prior standalone column-preview overview SHALL be retired. When the React build is missing or partial, that URL SHALL return the missing-build recovery response; no server-rendered project overview SHALL remain.

#### Scenario: Pipeline header renders repo identity
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an existing connected project while the complete React build is available
- **THEN** the Pipeline Surface header SHALL show the project name, root path, detected branch, language hints, framework hints, package manager hints, test command, run command, and relevant docs when available
- **AND** missing scalar values and collections SHALL render typed concise unavailable/empty states rather than `undefined` or raw JSON

#### Scenario: Missing or partial build returns the recovery response
- **WHEN** an authenticated operator opens `/projects/{project_id}` while the React build is missing or partial
- **THEN** the system SHALL return the missing-build recovery response at the same canonical URL
- **AND** it SHALL NOT render a server-rendered project overview, which no longer exists

#### Scenario: Pipeline header renders launch readiness
- **WHEN** an authenticated operator opens the Pipeline Surface
- **THEN** the system SHALL show the project's current Local Runner capability state and any missing launch capability reasons

#### Scenario: Missing project returns not found
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an unknown project id
- **THEN** the backend SHALL return not found
- **AND** React SHALL render a bounded error state rather than a partial project surface

### Requirement: Project overview links to existing workflows
The Pipeline Surface SHALL link to Portal workflows in the context of the selected project when that workflow is project-scoped, and SHALL link in-shell to the project's Execution Floor. Global and non-migrated settings/governance workflows SHALL remain reachable without duplicating their controls on the Pipeline Surface.

#### Scenario: Pipeline links to the Execution Floor and project workflows
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an active project
- **THEN** the Pipeline Surface SHALL link in-shell to the Execution Floor at `/projects/{project_id}/floor`
- **AND** task history, Sessions, Worker setup, and Project settings SHALL remain ordinary links to their existing Portal routes
- **AND** the Pipeline Surface SHALL not duplicate those workflow forms

#### Scenario: Archived Pipeline suppresses active board entry
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an archived project
- **THEN** the Pipeline Surface SHALL retain task history and session/evidence links
- **AND** it SHALL show Restore instead of active board, Floor, or launch entry points

### Requirement: Sidebar provides project repository switching
The system SHALL show connected project repositories in the Portal sidebar as first-class project navigation with distinct Pipeline and Execution Floor entries for the active project.

#### Scenario: Connected projects are visible in sidebar
- **WHEN** an authenticated operator opens any Portal page after connecting one or more projects
- **THEN** the sidebar SHALL list the connected project repositories by name
- **AND** each listed project SHALL link to `/projects/{project_id}`

#### Scenario: Active project and surface are highlighted
- **WHEN** an authenticated operator opens `/projects/{project_id}`, `/projects/{project_id}/floor`, or a compatibility `/projects/{project_id}/board` URL
- **THEN** the sidebar SHALL visually mark that project as active
- **AND** Pipeline and Execution Floor SHALL have distinct active-surface semantics

#### Scenario: Project navigation remains scoped from selected project
- **WHEN** an authenticated operator opens Pipeline or Execution Floor navigation for the active project
- **THEN** the system SHALL route to `/projects/{project_id}` or `/projects/{project_id}/floor` respectively

### Requirement: Project overview summarizes actionable repo state
The absorbed Pipeline project header and project-scoped Needs You/Planning state SHALL summarize the selected repository's useful operator state without a duplicate standalone overview. React SHALL render this state from bounded FastAPI projections and SHALL not infer readiness or lifecycle state locally.

#### Scenario: Pipeline shows next actions
- **WHEN** an authenticated operator opens the project Pipeline
- **THEN** the system SHALL show launch readiness, project-scoped Needs You decisions, planning work, and relevant workflow links when available
- **AND** each action SHALL link to or act through the authoritative workflow that handles it

#### Scenario: Pipeline uses authoritative refreshed state
- **WHEN** project capability, launch readiness, task counts, Needs You state, or archive state changes
- **THEN** React SHALL show values from refreshed FastAPI projections
- **AND** it SHALL not optimistically infer those values

#### Scenario: Pipeline does not duplicate workflow forms
- **WHEN** the Pipeline shows setup, session, history, or project-administration actions
- **THEN** it SHALL route the operator to existing workflow pages instead of duplicating adapter verification or project-administration forms

### Requirement: Project overview keeps repo identity visible but secondary
The absorbed Pipeline header SHALL keep repository identity and detected profile information visible in a compact project header while Pipeline planning and governed task work remain the primary page purpose.

#### Scenario: Repo profile remains visible in absorbed header
- **WHEN** an authenticated operator opens `/projects/{project_id}`
- **THEN** the Pipeline header SHALL show root path, branch, language/framework/package hints, test command, run command, and docs when available
- **AND** missing values SHALL use concise typed unavailable or empty states

#### Scenario: React repo profile remains bounded
- **WHEN** profile strings or collections are long or malformed
- **THEN** React SHALL render only the sanitized, truncated, typed profile projection defined by the React Portal shell contract
- **AND** it SHALL not render raw internal project metadata
