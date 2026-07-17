## ADDED Requirements

### Requirement: React views sanitize load errors
Every React view that loads state through an authenticated JSON handoff SHALL render a fixed, surface-specific message when that load fails. It SHALL NOT render backend-derived text — exception detail, response body, status text, or any part of them — whether raw or bounded to a length. Distinguishing a failed handoff from a negotiated action outcome is normative: a failed handoff is an exception and SHALL NOT reach the operator, while a negotiated action outcome carries text the backend authored for the operator and SHALL continue to be surfaced.

#### Scenario: A failed handoff shows a fixed message
- **WHEN** a React view's authenticated JSON handoff fails for any reason other than authentication
- **THEN** the view SHALL render a fixed message naming its own surface and offering retry
- **AND** the rendered text SHALL NOT contain the response detail, response body, or status text

#### Scenario: An unauthorized handoff names the auth boundary
- **WHEN** a React view's authenticated JSON handoff fails with an unauthorized status
- **THEN** the view SHALL render a fixed message stating that the surface requires sign-in

#### Scenario: Bounding backend text is not sanitizing it
- **WHEN** a React view derives its load-error message from backend text and truncates it to a maximum length
- **THEN** that SHALL NOT satisfy this requirement
- **AND** the view SHALL replace the backend text with a fixed message rather than shortening it

#### Scenario: No React view renders backend text in a load-error branch
- **WHEN** the frontend verification suite runs
- **THEN** it SHALL assert that no React view renders backend-derived error text in a load-error branch
- **AND** a view that reintroduces it SHALL fail that assertion rather than reaching an operator

#### Scenario: Negotiated action outcomes still reach the operator
- **WHEN** a React view submits an action that negotiates a JSON outcome and the backend returns its sanitized operator-facing error
- **THEN** the view SHALL surface that backend-authored message
- **AND** this requirement SHALL NOT cause authored operator guidance to be replaced by a fixed message

### Requirement: React owns not-found inside the shell
The React Portal shell SHALL render a branded not-found state for a route it owns navigation to but does not recognize, and that state SHALL route the operator to a canonical Portal URL rather than to a transitional `/app` alias. FastAPI SHALL remain responsible for unknown URLs requested from outside the shell; the shell SHALL NOT claim a catch-all route that would turn an unknown URL into a successful shell response.

#### Scenario: Unrecognized in-shell route shows a branded not-found
- **WHEN** the shell parses a route it does not recognize
- **THEN** it SHALL render a branded not-found state inside the Portal experience
- **AND** its recovery link SHALL target a canonical Portal URL rather than an `/app` alias

#### Scenario: Unknown URLs remain the backend's answer
- **WHEN** an unknown URL is requested from outside the shell
- **THEN** FastAPI SHALL return its existing not-found response
- **AND** the shell SHALL NOT be served for that URL
