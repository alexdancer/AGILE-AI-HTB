# control-plane-model-connection Specification

## Purpose
Define the model connection AGILE-AI-HTB uses for its own control-plane work, separate from any Worker Harness model configuration or credentials.

## Requirements

### Requirement: Control-plane model connection
The system SHALL provide a distinct direct control-plane model connection for AGILE-AI-HTB's own orchestration work, separate from Worker Harness model access and without requiring LiteLLM.

#### Scenario: Control-plane model configured
- **WHEN** the operator configures a control-plane provider, model, and required credentials or endpoint
- **THEN** AGILE-AI-HTB uses that direct provider API connection for task estimation, planning, recommendation, summaries, and reports

#### Scenario: Control-plane model missing
- **WHEN** no valid control-plane model connection is configured
- **THEN** AGILE-AI-HTB keeps local board and manual task workflows available but marks model-powered estimation, planning, and reporting as unavailable with a clear setup reason

### Requirement: Control-plane setup language
The system SHALL describe the AGILE-AI-HTB model connection as the control-plane model in UI and documentation rather than presenting it as a Worker Harness provider key.

#### Scenario: User views model setup
- **WHEN** the User opens settings or local setup documentation
- **THEN** the system distinguishes AGILE-AI-HTB control-plane model setup from OpenCode, Claude Code, Codex, or other Worker Harness setup

### Requirement: Backward-compatible provider key aliases
The system SHALL preserve existing provider key environment aliases where practical while treating explicit control-plane model settings as the canonical configuration and SHALL NOT copy one control-plane key into unrelated provider-specific environment variables.

#### Scenario: Explicit control-plane key exists
- **WHEN** `AGILE_AI_HTB_CONTROL_API_KEY` is present
- **THEN** the system uses it only for the configured control-plane/upstream provider client

#### Scenario: Legacy provider key env exists
- **WHEN** a legacy provider key environment variable is present and explicit control-plane credentials are absent
- **THEN** the system may use the legacy value for the control-plane model and labels it as compatibility behavior rather than Worker Harness configuration

#### Scenario: Provider env fan-out avoided
- **WHEN** the application starts with a configured control-plane API key
- **THEN** the system does not copy that key into unrelated provider-specific env vars such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `COHERE_API_KEY`, or `GROQ_API_KEY`

### Requirement: Control-plane connection test
The system SHALL allow the operator to verify the configured control-plane model without launching a Worker Harness.

#### Scenario: Control-plane test succeeds
- **WHEN** the operator runs a control-plane model connection test
- **THEN** the system records success evidence without exposing credentials and enables model-powered control-plane actions

#### Scenario: Control-plane test fails
- **WHEN** the configured control-plane model cannot be called
- **THEN** the system records a sanitized failure reason and keeps Worker Harness launch readiness independent from the failed control-plane test

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

### Requirement: Configurable Task Breakdown Model
The system SHALL provide a separately configurable Task Breakdown Model for Task Breakdown Agent work in the control-plane/orchestrator model layer, distinct from the Estimator LLM and from Worker Adapter models.

#### Scenario: Task Breakdown Model configured
- **WHEN** the operator configures a Task Breakdown Model
- **THEN** AGILE-AI-HTB uses that model for semantic task breakdown and proposed vertical-slice review generation
- **AND** usage is recorded as `task_breakdown` Orchestration Tokens rather than Worker execution spend

#### Scenario: Task Breakdown Model not explicitly configured
- **WHEN** no explicit Task Breakdown Model is configured
- **THEN** the system uses a documented control-plane fallback model setting
- **AND** still labels the usage as Task Breakdown Agent/control-plane spend, not Worker Adapter spend

#### Scenario: Worker Adapter model remains separate
- **WHEN** the Task Breakdown Agent runs before estimation
- **THEN** the system does not use OpenCode, Claude Code, Codex, Hermes, or other Worker Adapter model configuration as the Task Breakdown Model unless explicitly configured as a control-plane model connection
