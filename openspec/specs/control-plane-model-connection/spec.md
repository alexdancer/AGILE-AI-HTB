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
