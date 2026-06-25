## ADDED Requirements

### Requirement: Live control-plane connection editing
The system SHALL allow an authenticated operator to edit the control-plane provider, model, base URL, and API key environment variable name from the portal without restarting the application.

#### Scenario: Operator saves a new control-plane model
- **WHEN** the operator saves valid control-plane connection settings from the portal
- **THEN** the system persists the non-secret settings before changing runtime state
- **AND** subsequent control-plane requests use the new effective settings without requiring a server restart

#### Scenario: Config persistence fails
- **WHEN** the operator saves control-plane connection settings and the non-secret config file cannot be written
- **THEN** the system SHALL reject the save with a clear error
- **AND** the running control-plane settings SHALL remain unchanged

#### Scenario: Existing request is in flight
- **WHEN** a control-plane request is already in progress while the operator saves new settings
- **THEN** the system SHALL allow that in-flight request to finish using the settings it already started with
- **AND** new control-plane requests SHALL use the saved settings after the save succeeds

### Requirement: Control-plane preset selection
The system SHALL provide a small set of portal presets for common control-plane connection shapes while preserving free-text advanced fields.

#### Scenario: OpenAI preset selected
- **WHEN** the operator selects the OpenAI preset
- **THEN** the form SHALL set provider `openai` and model `gpt-5.4-mini`
- **AND** it SHALL leave the default OpenAI base URL behavior unless the operator overrides it

#### Scenario: Anthropic preset selected
- **WHEN** the operator selects the Anthropic preset
- **THEN** the form SHALL set provider `anthropic` and model `claude-haiku-4-5`
- **AND** it SHALL leave the default Anthropic base URL behavior unless the operator overrides it

#### Scenario: OpenAI-compatible preset selected
- **WHEN** the operator selects the OpenAI-compatible preset
- **THEN** the form SHALL set provider `openai-compatible`
- **AND** it SHALL require or expose free-text model and base URL fields for the compatible provider

### Requirement: Control-plane split-model default
The system SHALL default to applying the selected control-plane model to estimator and task-breakdown model settings while allowing the operator to preserve split-model settings.

#### Scenario: Default model coupling accepted
- **WHEN** the operator saves a control-plane model with the default coupling option enabled
- **THEN** the system SHALL persist the selected model as `control_plane_model`, `estimator_model`, and `task_breakdown_model`

#### Scenario: Split-model option preserved
- **WHEN** the operator saves a control-plane model with the coupling option disabled
- **THEN** the system SHALL persist the selected model as `control_plane_model`
- **AND** it SHALL preserve the existing `estimator_model` and `task_breakdown_model` values

### Requirement: Stale control-plane test status
The system SHALL mark previous control-plane connection test evidence as stale after saved control-plane connection settings change.

#### Scenario: Settings saved after previous successful test
- **WHEN** the operator saves changed control-plane connection settings after a prior successful connection test
- **THEN** the system SHALL display the control-plane setup state as needing a test
- **AND** it SHALL NOT present the previous test as proof that the new provider/model is reachable

#### Scenario: Operator tests changed settings
- **WHEN** the operator runs the control-plane connection test after changing settings
- **THEN** the system SHALL record sanitized success or failure evidence for the new effective provider/model
