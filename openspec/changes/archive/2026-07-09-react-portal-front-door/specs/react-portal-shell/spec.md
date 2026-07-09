## ADDED Requirements

### Requirement: React shell is the default authenticated landing
The authenticated Portal landing SHALL prefer the React shell when the frontend
is built, and SHALL fall back to the existing server-rendered landing when the
built frontend is absent, so a missing build never leaves the Portal without a
landing.

#### Scenario: Landing opens the React shell when built
- **WHEN** an authenticated operator opens the Portal root or completes login and the React frontend has been built
- **THEN** the system SHALL send the operator into the React Portal shell rather than the server-rendered landing

#### Scenario: Landing falls back when the build is absent
- **WHEN** an authenticated operator opens the Portal root or completes login and the built React frontend is not available
- **THEN** the system SHALL send the operator to the existing server-rendered landing
- **AND** the Portal SHALL remain usable without the React build

#### Scenario: Login still lands through the build-aware resolution
- **WHEN** an operator successfully logs in while portal auth is required
- **THEN** the existing login flow SHALL set the portal session and redirect to the build-aware landing
- **AND** no separate React login page SHALL be required by this change

### Requirement: React shell provides a project picker home
The React Portal shell SHALL provide a home view that lists the operator's
connected projects with entry points into each project's workspace and board, so
operators reach a project without typing a URL or a project id.

#### Scenario: Home lists connected projects
- **WHEN** an authenticated operator opens the React shell home with one or more connected projects
- **THEN** the shell SHALL list those projects with a way to open each project's React workspace and board

#### Scenario: Home has an actionable empty state
- **WHEN** an authenticated operator opens the React shell home with no connected projects
- **THEN** the shell SHALL show an empty state that links to the existing connect-project flow
- **AND** the home SHALL NOT be a dead end

#### Scenario: Project list uses an authenticated JSON handoff
- **WHEN** the React shell home requests the connected-project list
- **THEN** the system SHALL serve it from an authenticated FastAPI JSON endpoint that reuses existing project-list and task-count helpers
- **AND** an unauthenticated request to that endpoint SHALL be rejected by the existing portal authentication boundary

### Requirement: React shell navigates client-side between its surfaces
The React Portal shell SHALL let operators move between its home, project
workspace, and project board without manual URL entry, while deep links to
React-owned routes still resolve on a full page load.

#### Scenario: Selecting a project opens its workspace in-shell
- **WHEN** an operator selects a project from the React shell home
- **THEN** the shell SHALL open that project's workspace without the operator typing a URL

#### Scenario: Moving between workspace and board stays in-shell
- **WHEN** an operator opens the board from a project workspace and returns
- **THEN** the shell SHALL navigate between those surfaces client-side without requiring a manually entered URL

#### Scenario: Deep links still resolve
- **WHEN** an operator loads or refreshes a React-owned route such as a project workspace or board URL directly
- **THEN** the system SHALL serve the React shell for that route as it does today
