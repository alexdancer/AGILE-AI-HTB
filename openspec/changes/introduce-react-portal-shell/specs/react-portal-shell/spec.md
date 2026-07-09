## ADDED Requirements

### Requirement: FastAPI serves the React Portal shell
The system SHALL serve a built Vite React Portal shell from the existing FastAPI application without introducing a separate Node runtime server.

#### Scenario: Built React shell is available
- **WHEN** an authenticated operator opens a route owned by the React Portal shell after frontend assets have been built
- **THEN** FastAPI SHALL return the React shell `index.html`
- **AND** React asset files SHALL be served from the same FastAPI process

#### Scenario: React assets are missing
- **WHEN** an authenticated operator opens a React-owned route and the built frontend assets are not available
- **THEN** the system SHALL return a clear missing-build response or keep the existing Jinja route available for that surface
- **AND** the response SHALL NOT silently render a broken blank shell

#### Scenario: No separate frontend server is required in production
- **WHEN** AGILE-AI-HTB is served for normal operator use after the React frontend is built
- **THEN** the operator SHALL NOT need to run `vite`, `npm run dev`, or another Node server to use the migrated Portal surface

### Requirement: React owns only the first migrated project surface
The React Portal shell SHALL initially own only the selected project workspace plus project board shell while existing Jinja pages remain available for non-migrated surfaces.

#### Scenario: Project workspace opens in React shell
- **WHEN** an authenticated operator opens the migrated project workspace route for an existing connected project
- **THEN** the React shell SHALL show project identity, readiness summary, board entry, and actionable project state using data supplied by FastAPI

#### Scenario: Project board opens in React shell
- **WHEN** an authenticated operator opens the migrated project board route for an existing connected project
- **THEN** the React shell SHALL show project-scoped board columns, compact task cards, task intake entry points, queue/run status, and review/launch actions supported by existing backend paths

#### Scenario: Non-migrated pages remain available
- **WHEN** an authenticated operator opens setup, settings, sessions, alarms, dashboard, login, or another non-migrated Portal page
- **THEN** the existing FastAPI/Jinja page SHALL remain reachable unless that page is explicitly migrated by a later change

### Requirement: React uses authenticated JSON handoff endpoints
The React Portal shell SHALL load project workspace and project board state through authenticated FastAPI JSON endpoints that reuse existing view helpers and domain logic.

#### Scenario: Project state requires portal auth
- **WHEN** an unauthenticated request calls a React project workspace or board JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary

#### Scenario: JSON state reuses existing project behavior
- **WHEN** React requests project workspace or project board state for `{project_id}`
- **THEN** FastAPI SHALL derive the response from existing project, board, Worker readiness, budget, run automation, and review evidence helpers where those helpers already exist
- **AND** it SHALL NOT duplicate launch guardrail, estimation, Worker Run, budget, or review-disposition rules in frontend code

#### Scenario: Task actions stay backend-authoritative
- **WHEN** React submits task intake, estimate, launch, refresh, queue, review, archive, dismiss, or block actions
- **THEN** the request SHALL call existing FastAPI action paths or thin JSON wrappers around those paths
- **AND** backend validation SHALL remain authoritative for project binding, launch guardrails, budget acknowledgement, native usage acknowledgement, and review disposition

### Requirement: Frontend build checks are explicit
The system SHALL provide explicit commands or documented checks for building the React frontend and verifying the FastAPI app can serve the built shell.

#### Scenario: Frontend build succeeds
- **WHEN** the frontend build command is run from the repository
- **THEN** it SHALL produce static assets in the directory FastAPI is configured to serve

#### Scenario: Backend test suite covers shell serving
- **WHEN** the repository verification suite runs for this change
- **THEN** it SHALL include a check that FastAPI serves the React shell or reports missing assets clearly
