## ADDED Requirements

### Requirement: Curated control-plane model list has a single authoritative source
The curated control-plane provider/model choices SHALL be defined in a single authoritative source that every renderer consumes, so the Jinja settings page, the authenticated JSON read, and any React surface present the same curated dropdown without divergent copies.

#### Scenario: Every renderer reads the same curated list
- **WHEN** the Jinja control-plane page, the authenticated control-plane state JSON, and the React Control Plane Settings view render the curated model dropdown
- **THEN** each SHALL derive its curated provider/model choices from the same authoritative source
- **AND** no renderer SHALL hard-code an independent copy of the curated list

#### Scenario: Adding a curated model updates every renderer
- **WHEN** a curated provider/model choice is added to or removed from the authoritative source
- **THEN** the Jinja page, the JSON read, and the React view SHALL reflect that change without a per-renderer edit

### Requirement: Control-plane setup state has an authenticated placeholder-only JSON read
The Portal SHALL expose the current control-plane setup state through an authenticated JSON read that reuses the existing settings and connection-status computation. The read SHALL be placeholder-only: it SHALL report whether a key is present without ever serializing the control-plane API key value in any field.

#### Scenario: Control-plane state read requires authentication
- **WHEN** an unauthenticated caller requests the control-plane state read while portal auth is required
- **THEN** the Portal SHALL reject the request using the existing Portal authentication boundary
- **AND** SHALL NOT return control-plane state

#### Scenario: Read reports key presence without the key value
- **WHEN** an authenticated caller requests the control-plane state read
- **THEN** the response SHALL report `api_key_present` as a boolean derived from the effective environment for the configured key name
- **AND** it SHALL NOT include the control-plane API key value in any field, redacted or otherwise
- **AND** it SHALL report provider, model, base URL, api-key env name, estimator and task-breakdown models, legacy-env presence, environment-shadowed settings, the curated model list, and sanitized connection status

#### Scenario: Read distinguishes needs-test from offline
- **WHEN** the last saved settings changed but no connection test has run since
- **THEN** the read SHALL report connection status as `needs_test` rather than `offline` or `online`
- **AND** a recorded failed test SHALL report `offline` while a recorded successful test SHALL report `online`
