## ADDED Requirements

### Requirement: React is the build-aware default authenticated landing
The normal Portal landing SHALL use the React dashboard at `/app` when the complete built React shell is available. The system SHALL validate the React index and all referenced local React assets before choosing `/app`; when that validation fails, the normal landing SHALL remain the existing server-rendered first-project or `/projects` route. This promotion SHALL NOT remove explicit Jinja fallback routes or broaden React route ownership beyond `/app`, `/app/projects/{id}`, and `/app/projects/{id}/board`.

#### Scenario: Auth-disabled local root opens built React dashboard
- **WHEN** portal auth is not required and an operator opens `/` while the complete React build is available
- **THEN** the system SHALL redirect to `/app`
- **AND** the React shell SHALL render its dashboard inside the full Portal chrome

#### Scenario: Successful login opens built React dashboard
- **WHEN** portal auth is required and an operator submits a valid portal token while the complete React build is available
- **THEN** the system SHALL preserve the existing signed cookie behavior
- **AND** the successful login response SHALL redirect to `/app`

#### Scenario: Authenticated root opens built React dashboard
- **WHEN** portal auth is required and an authenticated operator opens `/` while the complete React build is available
- **THEN** the system SHALL redirect to `/app`

#### Scenario: Unauthenticated shared root still requires login
- **WHEN** portal auth is required and an unauthenticated operator opens `/`
- **THEN** the system SHALL redirect to `/login`
- **AND** build availability SHALL NOT bypass the existing authentication boundary

#### Scenario: Auth-disabled login and logout use normal landing
- **WHEN** portal auth is not required and an operator opens `/login`, submits a well-formed `/login` request containing the existing required token form field, or submits `/logout`
- **THEN** the system SHALL preserve existing harmless login/logout behavior
- **AND** it SHALL redirect to `/app` when the complete React build is available

#### Scenario: Missing React index falls back to Jinja landing
- **WHEN** a normal landing decision occurs and the React index is missing
- **THEN** the system SHALL redirect to the existing server-rendered first-project route when a connected project exists, otherwise `/projects`
- **AND** the operator SHALL NOT receive a blank shell or missing-build `503` as the default landing

#### Scenario: Partial React build falls back to Jinja landing
- **WHEN** the React index exists but one or more referenced local React assets are missing or invalid
- **THEN** the normal landing SHALL use the existing server-rendered first-project or `/projects` route
- **AND** the system SHALL NOT promote the partial shell

#### Scenario: Explicit React deep link retains clear missing-build behavior
- **WHEN** an authenticated operator explicitly opens a declared `/app` route while the React build is unavailable or partial
- **THEN** the existing clear missing-build response SHALL remain available
- **AND** the response SHALL provide a usable Jinja fallback link rather than a blank shell

#### Scenario: Non-migrated and fallback Jinja routes remain reachable
- **WHEN** an operator on the default React shell follows a link to Sessions, Alarms, Setup, Settings, task history, reports, Task Breakdown Review, or an explicit server-rendered fallback surface
- **THEN** the existing FastAPI/Jinja route SHALL remain reachable through ordinary full-page navigation
- **AND** no React client route SHALL claim that path

## REMOVED Requirements

### Requirement: Jinja remains the default authenticated landing

**Reason**: Portal chrome, Dashboard, project workspace, and normal governed AGILE Board workflow parity gates are complete, so the temporary Jinja-first default is no longer required when the complete React build exists.

**Migration**: Replace the unconditional Jinja landing with the build-aware React default requirement above. Preserve the same Jinja first-project or `/projects` destination as the automatic fallback when the React build is missing or partial.
