## MODIFIED Requirements

### Requirement: Placeholder-only control-plane secret guidance
The system SHALL support portal-managed control-plane API key values for the local operator setup path while continuing to avoid storing raw control-plane API key values in `.htb/config.toml` or exposing them in portal output.

#### Scenario: Env name changes to missing secret entry
- **WHEN** the operator saves a control-plane API key env name that is not present in `.htb/secrets.env`
- **THEN** the system SHALL add a placeholder entry for that env name to `.htb/secrets.env`
- **AND** it SHALL not overwrite any existing secret values

#### Scenario: Env name already has secret entry
- **WHEN** the operator saves a control-plane API key env name already present in `.htb/secrets.env`
- **THEN** the system SHALL preserve the existing value unless the operator submits a non-empty replacement API key value through the authenticated portal form
- **AND** it SHALL not print or expose the existing value

#### Scenario: Portal saves control-plane API key value
- **WHEN** an authenticated local operator submits a non-empty control-plane API key value through the control-plane settings portal
- **THEN** the system SHALL write that value to ignored `.htb/secrets.env` under the configured control-plane API key env name
- **AND** the system SHALL not write the raw key value to `.htb/config.toml`

#### Scenario: Common setup hides env mechanics
- **WHEN** an operator uses the normal control-plane settings portal flow
- **THEN** the system SHALL present provider, model, and API key entry as the primary setup controls
- **AND** the API key env-name field SHALL be hidden, collapsed, or otherwise presented as advanced compatibility configuration rather than a required manual setup step
