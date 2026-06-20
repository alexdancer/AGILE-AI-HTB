## MODIFIED Requirements

### Requirement: Control-plane model connection
The system SHALL provide a distinct direct control-plane model connection for AGILE-AI-HTB's own orchestration work, separate from Worker Harness model access and without requiring LiteLLM.

#### Scenario: Control-plane model configured
- **WHEN** the operator configures a control-plane provider, model, and required credentials or endpoint
- **THEN** AGILE-AI-HTB uses that direct provider API connection for task estimation, planning, recommendation, summaries, and reports

#### Scenario: Control-plane model missing
- **WHEN** no valid control-plane model connection is configured
- **THEN** AGILE-AI-HTB keeps local board and manual task workflows available but marks model-powered estimation, planning, and reporting as unavailable with a clear setup reason

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
