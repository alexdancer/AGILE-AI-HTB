## ADDED Requirements

### Requirement: Operator initialization writes non-secret config
The system SHALL provide an `htb init` command that creates a local operator configuration file containing non-secret AGILE-AI-HTB settings.

#### Scenario: Initialize local harness config
- **WHEN** an operator runs `htb init` with default local choices
- **THEN** the system SHALL create `.htb/config.toml` with non-secret settings for database path, guardrails path, control-plane provider/model, control-plane API key env name, portal token env name, and Local Runner enablement

#### Scenario: Secrets are not persisted
- **WHEN** `htb init` needs a portal token value or control-plane API key value
- **THEN** the system SHALL write secret values or placeholders to ignored `.htb/secrets.env` and print edit guidance instead of writing raw secret values into `.htb/config.toml`

### Requirement: Serve uses configured defaults
The system SHALL load operator configuration when starting the portal and resolve settings with precedence `CLI flag > environment variable > .htb/config.toml > built-in default`.

#### Scenario: Serve reads config without repeated exports
- **WHEN** `.htb/config.toml` defines Local Runner enabled and a control-plane model, and the operator runs `htb serve` without those flags or env vars
- **THEN** the portal SHALL start with Local Runner enabled and the configured control-plane model

#### Scenario: Environment overrides config
- **WHEN** `.htb/config.toml` defines a control-plane model and the environment defines `AGILE_AI_HTB_CONTROL_MODEL`
- **THEN** the effective control-plane model SHALL use the environment value

#### Scenario: CLI overrides config and environment
- **WHEN** a CLI option exists for a setting and the same setting is present in environment and `.htb/config.toml`
- **THEN** the effective setting SHALL use the CLI option value

### Requirement: Readiness check reports operator setup state
The system SHALL provide an `htb check` command that reports local harness readiness with `PASS`, `WARN`, and `FAIL` lines.

#### Scenario: Required secrets are missing
- **WHEN** the configured portal token env var or control-plane API key env var is not present
- **THEN** `htb check` SHALL report a `FAIL` line naming the missing env var and SHALL not print secret values

#### Scenario: Control-plane model is reachable
- **WHEN** required control-plane configuration is present and the provider test succeeds
- **THEN** `htb check` SHALL report `PASS` for the control-plane provider/model connection

#### Scenario: Worker adapter is diagnostic only
- **WHEN** a Worker Adapter is detected but its tracking mode is `observed_only`
- **THEN** `htb check` SHALL report `WARN` that the adapter is diagnostic-only and not normal board-launchable

#### Scenario: Worker adapter is launch-ready
- **WHEN** a Worker Adapter is verified with `proxy_governed` or budget-authoritative `native_usage`
- **THEN** `htb check` SHALL report `PASS` for Worker launch readiness and name the adapter identity separately from the tracking mode

### Requirement: Documentation uses operator setup path
The system SHALL document the operator setup flow as the primary local startup path and keep demo seeding as an optional follow-up.

#### Scenario: Local setup docs avoid export-heavy startup
- **WHEN** an operator reads the local setup or demo runbook
- **THEN** the startup path SHALL prefer `htb init`, editing `.htb/secrets.env`, `htb serve`, and `htb check` over a list of unrelated setup exports
