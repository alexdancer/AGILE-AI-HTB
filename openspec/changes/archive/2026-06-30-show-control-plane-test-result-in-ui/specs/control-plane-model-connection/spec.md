## MODIFIED Requirements

### Requirement: Control-plane connection test
The system SHALL allow the operator to verify the configured control-plane model without launching a Worker Harness, and SHALL present browser-initiated test results inside the Control Plane settings UI rather than navigating to a raw JSON result page.

#### Scenario: Control-plane test succeeds
- **WHEN** the operator runs a control-plane model connection test
- **THEN** the system records success evidence without exposing credentials and enables model-powered control-plane actions

#### Scenario: Control-plane test fails
- **WHEN** the configured control-plane model cannot be called
- **THEN** the system records a sanitized failure reason and keeps Worker Harness launch readiness independent from the failed control-plane test

#### Scenario: Browser test returns to settings UI
- **WHEN** an authenticated operator submits the Control Plane connection test from the Portal settings page
- **THEN** the system SHALL record the sanitized test result
- **AND** the response SHALL return the operator to `/settings/control-plane` instead of rendering a JSON response page
- **AND** the settings page SHALL show a concise success or failure result for the latest test

#### Scenario: Settings UI preserves auditable raw evidence
- **WHEN** the Control Plane settings page displays a recorded connection test
- **THEN** the page SHALL show the primary result as readable status fields such as status, provider, model, token usage, or sanitized error
- **AND** full sanitized raw details SHALL remain available behind a native disclosure or equivalent secondary detail view
- **AND** raw control-plane API key values SHALL NOT be displayed

#### Scenario: API test remains JSON
- **WHEN** an authenticated API client posts a Control Plane connection test request that prefers JSON
- **THEN** the system SHALL return the machine-readable JSON result with the recorded sanitized status
