## MODIFIED Requirements

### Requirement: Operator initialization writes non-secret config
The system SHALL provide an `htb init` command that creates complete repo-local AGILE-AI-HTB state while keeping configuration non-secret and preserving existing local data.

#### Scenario: Initialize local harness state from repository root
- **WHEN** an operator runs `htb init` with default local choices from a repository root
- **THEN** the system SHALL create `.htb/config.toml` with non-secret settings for database path, guardrails path, control-plane provider/model, control-plane API key env name, portal token env name, and Local Runner enablement
- **AND** the system SHALL create `.htb/secrets.env` for local secret values or placeholders
- **AND** the system SHALL create `.htb/guardrails.yaml`
- **AND** the system SHALL create or migrate the configured SQLite database, defaulting to `.htb/harness.db`

#### Scenario: Initialize from repository subdirectory
- **WHEN** an operator runs `htb init` with default paths from inside a Git repository subdirectory
- **THEN** the system SHALL initialize default `.htb/` state at the Git repository root
- **AND** the command output SHALL identify the initialized root path

#### Scenario: Initialize outside Git repository
- **WHEN** an operator runs `htb init` with default paths outside a Git repository
- **THEN** the system SHALL initialize default `.htb/` state in the current working directory
- **AND** the command output SHALL identify the initialized root path

#### Scenario: Secrets are not persisted in config
- **WHEN** `htb init` needs a portal token value or control-plane API key value
- **THEN** the system SHALL write secret values or placeholders to ignored `.htb/secrets.env` and print edit guidance instead of writing raw secret values into `.htb/config.toml`

#### Scenario: Existing local state is preserved
- **WHEN** `.htb/config.toml`, `.htb/secrets.env`, `.htb/guardrails.yaml`, or `.htb/harness.db` already exists and the operator reruns `htb init`
- **THEN** the system SHALL preserve existing configured values and database data
- **AND** it SHALL apply missing defaults or database migrations idempotently

#### Scenario: Local harness state is protected from Git tracking
- **WHEN** `htb init` initializes local `.htb/` state
- **THEN** the system SHALL ensure `.htb/` local state is ignored by Git without requiring the operator to hand-edit ignore rules
