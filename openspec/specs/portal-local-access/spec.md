# portal-local-access Specification

## Purpose
TBD - created by archiving change skip-local-portal-login. Update Purpose after archive.
## Requirements
### Requirement: Loopback Portal access skips token login
The system SHALL allow the default loopback local Portal run to be used without submitting a portal login token.

#### Scenario: Default loopback root opens Portal landing
- **WHEN** an operator starts the Portal through the default local `htb serve` loopback bind
- **THEN** `GET /` SHALL redirect to the normal Portal landing page without requiring a login cookie or bearer token

#### Scenario: Loopback protected page opens without cookie
- **WHEN** portal auth is not required for the local loopback run
- **AND** the operator requests a Portal HTML page such as `/projects` without a cookie or bearer token
- **THEN** the page SHALL render instead of returning `401 missing portal authentication`

### Requirement: Shared Portal access keeps token auth
The system SHALL keep portal token authentication required when the Portal is reachable beyond the operator's loopback machine or auth is explicitly required.

#### Scenario: Non-loopback bind requires auth
- **WHEN** the Portal is started with a non-loopback bind such as `0.0.0.0` or a hosted/reverse-proxy auth-required setting
- **THEN** protected Portal pages SHALL require the existing bearer token or signed portal cookie
- **AND** unauthenticated requests SHALL return the existing unauthorized response

#### Scenario: Auth-required login still sets cookie
- **WHEN** portal auth is required
- **AND** the operator submits the correct portal token to `/login`
- **THEN** the system SHALL set the existing signed HttpOnly portal cookie
- **AND** redirect to the normal Portal landing page

### Requirement: Login route remains compatible
The system SHALL keep `/login` available for auth-required deployments while avoiding it as mandatory local-loopback first-run friction.

#### Scenario: Login route redirects when auth disabled
- **WHEN** portal auth is not required
- **AND** the operator opens `/login`
- **THEN** the system SHALL redirect to the normal Portal landing page instead of showing a token form

#### Scenario: Logout in no-auth mode is harmless
- **WHEN** portal auth is not required
- **AND** the operator submits `/logout`
- **THEN** the system SHALL clear any existing portal cookie if present
- **AND** redirect to the normal Portal landing page

