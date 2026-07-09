## MODIFIED Requirements

### Requirement: Jinja remains the default authenticated landing
The authenticated Portal landing SHALL use the existing server-rendered
Jinja surface while the React shell lacks Portal chrome, dashboard, and
AGILE Board parity. The React shell SHALL remain reachable at `/app`,
`/app/projects/{id}`, and `/app/projects/{id}/board` as an
experimental/migrated surface, but SHALL NOT
be the default landing for root, login, or logout until a later change
re-enables it after parity gates pass. A missing or partial React build
SHALL never leave the Portal without a usable landing.

#### Scenario: Landing uses the server-rendered Portal when the React build is present
- **WHEN** an authenticated operator opens the Portal root or completes login and the React frontend has been built
- **THEN** the system SHALL send the operator to the existing server-rendered landing (`/projects` or `/projects/{first-connected}`)
- **AND** the system SHALL NOT redirect to `/app` as the default landing

#### Scenario: Landing uses the server-rendered Portal when the build is absent
- **WHEN** an authenticated operator opens the Portal root or completes login and the built React frontend is not available
- **THEN** the system SHALL send the operator to the existing server-rendered landing (`/projects` or `/projects/{first-connected}`)
- **AND** the Portal SHALL remain usable without the React build

#### Scenario: Login still lands on the server-rendered Portal
- **WHEN** an operator successfully logs in while portal auth is required
- **THEN** the existing login flow SHALL set the portal session and redirect to the server-rendered landing
- **AND** no separate React login page SHALL be required by this change

#### Scenario: React shell remains reachable as a non-default surface
- **WHEN** an authenticated operator navigates explicitly to one of the three declared React routes after the frontend has been built
- **THEN** the system SHALL serve the React Portal shell for that route
- **AND** the system SHALL NOT remove or rename those declared routes or their authenticated JSON handoff endpoints as part of this rollback

#### Scenario: Missing or partial React build never renders a blank shell
- **WHEN** an operator navigates explicitly to `/app` and the React build is missing or references unavailable assets
- **THEN** the system SHALL return a clear missing-build response
- **AND** the response SHALL NOT silently render a broken blank shell