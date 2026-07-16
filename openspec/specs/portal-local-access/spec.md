# portal-local-access Specification

## Purpose
TBD - created by archiving change skip-local-portal-login. Update Purpose after archive.
## Requirements
### Requirement: Loopback Portal access skips token login
The system SHALL allow the default loopback local Portal run to be used without submitting a portal login token.

#### Scenario: Default loopback root opens Portal landing
- **WHEN** an operator starts the Portal through the default local `foremanctl serve` loopback bind
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
The system SHALL keep `/login` available for auth-required deployments while avoiding it as mandatory local-loopback first-run friction. `/login` SHALL keep its existing URL, form method, token field, cookie behavior, and redirect targets; only its rendering and failure presentation are defined by this specification. Normal login SHALL remain server-rendered rather than becoming a React-owned surface, because the server-rendered login is the only entry point available when the React build cannot load.

#### Scenario: Login route redirects when auth disabled
- **WHEN** portal auth is not required
- **AND** the operator opens `/login`
- **THEN** the system SHALL redirect to the normal Portal landing page instead of showing a token form

#### Scenario: Logout in no-auth mode is harmless
- **WHEN** portal auth is not required
- **AND** the operator submits `/logout`
- **THEN** the system SHALL clear any existing portal cookie if present
- **AND** redirect to the normal Portal landing page

#### Scenario: Successful login is unchanged by the recovery surface
- **WHEN** an operator submits the correct portal token to `/login` while portal auth is required
- **THEN** the system SHALL set the existing signed HttpOnly portal cookie and redirect to the normal Portal landing page
- **AND** the landing SHALL remain the existing build-aware target rather than being pinned to a server-rendered page

### Requirement: The login page is the self-contained Portal Recovery Surface
The server-rendered login page SHALL be the Portal Recovery Surface: the way into the Portal when the React build is missing, partial, or has not loaded. It SHALL render standalone and branded, without authenticated Portal navigation, and SHALL NOT depend on the shared template chrome or any other template that the Jinja retirement change removes. It SHALL NOT query or expose project, task, session, or any other operator data before authentication succeeds.

#### Scenario: Login renders without the shared chrome
- **WHEN** an operator opens `/login` while portal auth is required
- **THEN** the page SHALL render its own standalone branded layout
- **AND** it SHALL NOT render the Portal sidebar, project list, navigation groups, or logout control
- **AND** it SHALL NOT inherit from a template that the Jinja retirement change removes

#### Scenario: Login survives retirement of the duplicated surfaces
- **WHEN** the Jinja retirement change removes the duplicated operator templates
- **THEN** the login page SHALL continue to render unchanged
- **AND** it SHALL depend on no removed template, layout, or shared style block

#### Scenario: Login exposes no operator data before authentication
- **WHEN** an unauthenticated operator opens `/login`
- **THEN** the response SHALL NOT contain connected project names, root paths, task counts, session evidence, or adapter configuration
- **AND** the page SHALL NOT require a query against operator data to render

### Requirement: Failed login reports failure to the operator
A rejected `/login` submission SHALL re-render the login page with a sanitized error the operator can act on, rather than returning a raw exception body. The error SHALL NOT reveal whether the configured token is absent, whether a submitted token partially matched, or any other detail that distinguishes one rejection cause from another. The existing constant-time comparison and unauthorized status SHALL remain unchanged.

#### Scenario: Wrong token re-renders the form with a sanitized error
- **WHEN** an operator submits an incorrect portal token to `/login` while portal auth is required
- **THEN** the system SHALL render the login page again with a sanitized error message
- **AND** the response SHALL NOT be a raw JSON exception body
- **AND** the response SHALL preserve the existing unauthorized status code
- **AND** the submitted token SHALL NOT be reflected in the response

#### Scenario: Rejection causes are indistinguishable
- **WHEN** login is rejected because the submitted token is wrong, because the submitted token is empty, because the token field is absent from the submission, or because no portal token is configured on the server
- **THEN** the operator-facing error SHALL be the same in every case
- **AND** it SHALL NOT state which cause applied

#### Scenario: A submission without the token field is an ordinary rejection
- **WHEN** a `/login` submission omits the token field entirely while portal auth is required
- **THEN** the system SHALL treat it as a rejected login and render the login page with the same sanitized error
- **AND** it SHALL NOT return a field-validation response that distinguishes an absent field from an incorrect token

#### Scenario: Token comparison remains constant-time
- **WHEN** a login submission is checked against the configured portal token
- **THEN** the system SHALL preserve the existing constant-time comparison
- **AND** the failure rendering SHALL NOT introduce an earlier return that distinguishes a partially matching token

