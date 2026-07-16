## MODIFIED Requirements

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
