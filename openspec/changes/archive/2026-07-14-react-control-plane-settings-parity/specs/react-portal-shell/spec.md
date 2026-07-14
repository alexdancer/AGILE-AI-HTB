## ADDED Requirements

### Requirement: React Control Plane Settings JSON is authenticated, exact, and bounded
FastAPI SHALL expose a new authenticated JSON handoff for Control Plane Settings that requires Portal authentication and reuses the existing settings and connection-status computation. The response SHALL be placeholder-only and preserve every field the operator needs to configure the connection and read its test status without recomputing control-plane rules in the frontend.

#### Scenario: Control-plane handoff requires authentication
- **WHEN** an unauthenticated caller requests the authenticated React Control Plane Settings JSON handoff while portal auth is required
- **THEN** FastAPI SHALL reject the request using the Portal authentication boundary
- **AND** SHALL NOT return control-plane settings data

#### Scenario: Control-plane JSON is placeholder-only and exact
- **WHEN** an authenticated caller requests the React Control Plane Settings JSON handoff
- **THEN** the response SHALL include provider, model, base URL, api-key env name, `api_key_present` boolean, estimator model, task-breakdown model, legacy-env presence, environment-shadowed settings, the curated model list from the authoritative source, and a sanitized connection status carrying its `online`/`needs_test`/`offline` state
- **AND** it SHALL NOT include the control-plane API key value in any field
- **AND** absent optional values SHALL be typed `null` rather than fabricated defaults

### Requirement: React negotiates the control-plane save and test outcomes
The existing `POST /settings/control-plane` and `POST /settings/control-plane/test` actions SHALL return a bounded, sanitized JSON outcome to React/JSON callers while preserving the current Jinja redirects for HTML callers. Config persistence, secret storage, live apply, stale-test marking, and the connection test SHALL remain authoritative for both caller types.

#### Scenario: React caller receives a JSON save outcome
- **WHEN** a React/JSON caller submits valid control-plane settings
- **THEN** FastAPI SHALL persist and apply them using the existing authoritative behavior and mark prior test evidence as needing a new test
- **AND** SHALL return a bounded JSON outcome sufficient for React to refresh authoritative state
- **AND** the outcome SHALL NOT contain the control-plane API key value

#### Scenario: React save error is sanitized
- **WHEN** a React/JSON caller's save fails while writing config or secret storage
- **THEN** FastAPI SHALL return a sanitized error outcome envelope
- **AND** raw filesystem paths or exception detail SHALL NOT reach the operator

#### Scenario: React caller receives a JSON test outcome
- **WHEN** a React/JSON caller runs the control-plane connection test
- **THEN** FastAPI SHALL execute the existing test against the last-saved-and-applied config and record sanitized success or failure evidence
- **AND** SHALL return a bounded JSON outcome carrying the resulting `online` or `offline` status

#### Scenario: HTML callers keep the redirects
- **WHEN** a browser form caller submits the save or test action without negotiating `application/json`
- **THEN** FastAPI SHALL preserve the existing redirect behavior for that action
- **AND** the negotiated JSON path SHALL NOT alter that HTML behavior

### Requirement: React Control Plane Settings navigates inside the shell
React SHALL render Control Plane Settings inside the shared Portal chrome on the canonical `/settings/control-plane` URL when the complete build is available, and FastAPI SHALL render the existing Jinja page at the same URL when the build is missing or partial. The view SHALL preserve provider-filtered curated model selection with a custom-model path, placeholder-only key entry, the three-state connection status, and the environment-shadow warning.

#### Scenario: Built canonical route opens React Control Plane Settings in-shell
- **WHEN** an authenticated operator opens `/settings/control-plane` while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell and render Control Plane Settings inside the full Portal chrome
- **AND** React SHALL request the authenticated control-plane JSON for its form and status

#### Scenario: Missing or partial build keeps canonical Control Plane Settings in Jinja
- **WHEN** an authenticated operator opens `/settings/control-plane` while the React build is missing or partial
- **THEN** FastAPI SHALL render the existing Jinja control-plane page at the same canonical URL
- **AND** it SHALL NOT return a blank shell or require an alternate fallback URL

#### Scenario: Key input is placeholder-only and blank keeps the existing key
- **WHEN** the React Control Plane Settings form renders
- **THEN** the API key input SHALL be a password field that is empty by default and never prefilled with the stored key
- **AND** submitting the form with the key field blank SHALL preserve the existing stored key through the existing backend behavior

#### Scenario: Dirty form disables the connection test
- **WHEN** the operator has unsaved edits in the React Control Plane Settings form
- **THEN** React SHALL disable the Test action and show an inline hint to save before testing
- **AND** after a successful save the form SHALL become pristine and the Test action SHALL re-enable with status shown as `needs_test`

#### Scenario: Provider selection filters the curated model dropdown
- **WHEN** the operator changes the provider in the React form
- **THEN** the curated model dropdown SHALL show only that provider's curated choices and otherwise expose the custom-model path
- **AND** an existing saved model outside the curated choices SHALL be preserved through the custom-model path

#### Scenario: Save stays on page with inline outcome and authoritative refetch
- **WHEN** an operator saves control-plane settings from the React view and the save succeeds
- **THEN** React SHALL show an inline success outcome without leaving the page
- **AND** React SHALL refetch authoritative control-plane state rather than optimistically trusting the submitted values
