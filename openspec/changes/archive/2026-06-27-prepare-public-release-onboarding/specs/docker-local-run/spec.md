## ADDED Requirements

### Requirement: Docker no-secret trial path
The Docker local run documentation SHALL provide a no-secret trial path that proves containerized Control Plane/Portal startup and persistence without requiring provider credentials.

#### Scenario: Operator tries Docker without provider key
- **WHEN** an operator follows the Docker no-secret trial path
- **THEN** the documented path SHALL verify image build/start, `/health`, `/login`, and persisted SQLite state
- **AND** it SHALL state that model-powered estimates, real provider tests, and real Worker verification require later credential setup

## MODIFIED Requirements

### Requirement: Docker Worker Adapter boundary
Docker documentation SHALL distinguish containerized Control Plane readiness from host-native Worker Adapter readiness and SHALL NOT imply that Docker startup can launch host-installed coding CLIs by default.

#### Scenario: Host Worker access not implied
- **WHEN** an operator reads Docker setup documentation
- **THEN** the documentation SHALL state that Docker startup does not automatically provide access to host-installed OpenCode, Claude Code, Codex, Hermes, host repo paths, or host credentials
- **AND** Worker launch readiness SHALL remain governed by configured Worker Adapter and tracking-mode checks

#### Scenario: Docker quickstart preserves model-layer split
- **WHEN** Docker docs describe control-plane provider/model/API-key configuration
- **THEN** they SHALL identify those settings as Control Plane settings for AGILE-AI-HTB estimation, planning, summaries, and reports
- **AND** they SHALL state that native Worker CLI auth is separate from Docker control-plane env vars
