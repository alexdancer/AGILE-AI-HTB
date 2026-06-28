## ADDED Requirements

### Requirement: Docker setup uses operator setup semantics
The system SHALL document Docker startup as an operator setup path that preserves AGILE-AI-HTB control-plane configuration and secret boundaries.

#### Scenario: Docker docs use control-plane model language
- **WHEN** an operator reads Docker setup documentation
- **THEN** the documentation SHALL describe model env vars as AGILE-AI-HTB control-plane settings for estimation, planning, summaries, and reports
- **AND** SHALL NOT present those env vars as OpenCode, Claude Code, Codex, Hermes, or other Worker Adapter credentials

#### Scenario: Docker docs keep secrets out of committed files
- **WHEN** Docker setup requires a Portal token or provider API key
- **THEN** the documentation SHALL instruct the operator to provide values through environment variables or local uncommitted Compose overrides
- **AND** SHALL NOT require committing raw secrets

#### Scenario: Docker can run setup commands inside container
- **WHEN** the Docker service is running
- **THEN** the documented setup flow SHALL show how to run `htb check` inside the container without installing AGILE-AI-HTB on the host

#### Scenario: Docker env uses canonical control-plane names
- **WHEN** Docker docs or Compose examples configure the control-plane model connection
- **THEN** they SHALL prefer `AGILE_AI_HTB_CONTROL_PROVIDER`, `AGILE_AI_HTB_CONTROL_MODEL`, optional `AGILE_AI_HTB_CONTROL_BASE_URL`, and `AGILE_AI_HTB_CONTROL_API_KEY`
- **AND** they SHALL keep `TOKEN_TRACKER_PORTAL_TOKEN` as the Portal login token env var
