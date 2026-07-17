## MODIFIED Requirements

### Requirement: React owns only the migrated project surfaces
The React Portal shell SHALL own its dashboard home, selected project workspace, and project board workflow while existing Jinja pages remain available for non-migrated workflows and as dashboard/board fallback.

#### Scenario: Unknown React paths are not claimed
- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{project_id}`, or `/app/projects/{project_id}/board`
- **THEN** the system SHALL return not found instead of silently rendering a React surface

#### Scenario: Dashboard opens in React shell
- **WHEN** an authenticated operator explicitly opens `/app`
- **THEN** the React shell SHALL show dashboard-equivalent operator state using data supplied by FastAPI
- **AND** the existing Jinja `/dashboard` route SHALL remain reachable as a fallback

#### Scenario: Project workspace opens in React shell
- **WHEN** an authenticated operator opens the migrated project workspace route for an existing connected project
- **THEN** the React shell SHALL show project identity, readiness summary, board entry, and actionable project state using data supplied by FastAPI

#### Scenario: Project board completes normal workflow in React shell
- **WHEN** an authenticated operator opens the migrated project board route for an existing connected project
- **THEN** the React shell SHALL show project-scoped board columns, compact task cards, queue/run status, task intake, launch, refresh, review, archive/dismiss, and bounded task evidence controls using authenticated FastAPI data and actions
- **AND** backend validation SHALL remain authoritative for every workflow decision

#### Scenario: Jinja board remains reachable as fallback
- **WHEN** an operator needs the server-rendered board, a Task Breakdown Review, task history, session/report evidence, or another non-migrated Portal workflow
- **THEN** the existing FastAPI/Jinja page SHALL remain reachable
- **AND** the React board SHALL not require the Jinja board to complete its normal in-board workflow

#### Scenario: Non-migrated pages remain available
- **WHEN** an authenticated operator opens setup, settings, sessions, alarms, login, or another non-migrated Portal page
- **THEN** the existing FastAPI/Jinja page SHALL remain reachable unless that page is explicitly migrated by a later change

### Requirement: Jinja remains the default authenticated landing
The authenticated Portal landing SHALL use the existing server-rendered Jinja surface until an explicit later React default-enable change verifies and enables the default-landing parity gate. The React shell SHALL remain reachable at `/app`, `/app/projects/{id}`, and `/app/projects/{id}/board`; completing project-board workflow parity alone SHALL NOT change root, login, or logout routing. A missing or partial React build SHALL never leave the Portal without a usable landing.

#### Scenario: Landing remains server-rendered before explicit default enable
- **WHEN** an authenticated operator opens the Portal root or completes login before a later default-enable change is accepted
- **THEN** the system SHALL send the operator to the existing server-rendered landing (`/projects` or `/projects/{first-connected}`)
- **AND** the system SHALL NOT redirect to `/app` by default even when the React project board is workflow-capable

#### Scenario: React routes remain explicit and build-safe
- **WHEN** an authenticated operator explicitly opens a declared React route and built assets are available
- **THEN** the system SHALL serve the React Portal shell
- **AND** when the build is missing or partial, the system SHALL return a clear usable fallback response rather than a blank shell
