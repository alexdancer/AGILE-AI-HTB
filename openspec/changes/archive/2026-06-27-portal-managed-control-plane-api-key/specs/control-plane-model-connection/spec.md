## ADDED Requirements

### Requirement: Portal-managed control-plane API key entry
The system SHALL allow an authenticated operator to provide the control-plane API key value from the control-plane model settings portal without requiring manual environment variable export or manual `.htb/secrets.env` editing for the common local setup path.

#### Scenario: Operator saves a new control-plane key
- **WHEN** an authenticated operator enters provider/model settings and a non-empty control-plane API key value in the portal
- **THEN** the system SHALL store the key value in ignored local secret storage for the configured control-plane API key name
- **AND** the system SHALL NOT store the key value in `.htb/config.toml`
- **AND** subsequent control-plane requests SHALL be able to load the saved key without a server restart

#### Scenario: Operator leaves key blank
- **WHEN** an authenticated operator saves control-plane settings with the API key field blank
- **THEN** the system SHALL preserve any existing stored control-plane API key value
- **AND** the system SHALL NOT replace the stored value with an empty string or placeholder

#### Scenario: Portal redacts key values
- **WHEN** the control-plane settings page, save response, connection status, logs, or test evidence are rendered
- **THEN** the system SHALL show whether a key is present without displaying the raw control-plane API key value

#### Scenario: Connection test remains explicit
- **WHEN** an authenticated operator saves a new control-plane API key value
- **THEN** the system SHALL mark prior connection test evidence as needing a new test
- **AND** the system SHALL NOT require the provider connection test to pass before saving the local settings and secret
