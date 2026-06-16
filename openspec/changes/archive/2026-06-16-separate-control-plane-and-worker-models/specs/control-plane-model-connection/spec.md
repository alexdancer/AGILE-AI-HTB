## ADDED Requirements

### Requirement: Control-plane model connection
The system SHALL provide a distinct control-plane model connection for AGILE-AI-HTB's own orchestration work, separate from Worker Harness model access.

#### Scenario: Control-plane model configured
- **WHEN** the operator configures a control-plane provider, model, and required credentials or endpoint
- **THEN** AGILE-AI-HTB uses that connection for task estimation, planning, recommendation, summaries, and reports

#### Scenario: Control-plane model missing
- **WHEN** no valid control-plane model connection is configured
- **THEN** AGILE-AI-HTB keeps local board and manual task workflows available but marks model-powered estimation, planning, and reporting as unavailable with a clear setup reason

### Requirement: Control-plane setup language
The system SHALL describe the AGILE-AI-HTB model connection as the control-plane model in UI and documentation rather than presenting it as a Worker Harness provider key.

#### Scenario: User views model setup
- **WHEN** the User opens settings or local setup documentation
- **THEN** the system distinguishes AGILE-AI-HTB control-plane model setup from OpenCode, Claude Code, Codex, or other Worker Harness setup

### Requirement: Backward-compatible provider key aliases
The system SHALL preserve existing provider key environment aliases where practical while treating explicit control-plane model settings as the canonical configuration.

#### Scenario: Legacy provider key env exists
- **WHEN** a legacy provider key environment variable is present and explicit control-plane credentials are absent
- **THEN** the system may use the legacy value for the control-plane model and labels it as compatibility behavior rather than Worker Harness configuration

### Requirement: Control-plane connection test
The system SHALL allow the operator to verify the configured control-plane model without launching a Worker Harness.

#### Scenario: Control-plane test succeeds
- **WHEN** the operator runs a control-plane model connection test
- **THEN** the system records success evidence without exposing credentials and enables model-powered control-plane actions

#### Scenario: Control-plane test fails
- **WHEN** the configured control-plane model cannot be called
- **THEN** the system records a sanitized failure reason and keeps Worker Harness launch readiness independent from the failed control-plane test
