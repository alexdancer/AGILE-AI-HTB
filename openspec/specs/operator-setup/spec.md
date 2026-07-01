# operator-setup Specification

## Purpose
Define the local operator setup flow for AGILE-AI-HTB, including non-secret configuration, ignored secret guidance, readiness checks, and portal-driven configuration updates.
## Requirements
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
The system SHALL provide an `htb check` command that reports local harness readiness with redacted, support-friendly `PASS`, `WARN`, and `FAIL` lines plus actionable remediation for the public onboarding path.

#### Scenario: Required secrets are missing
- **WHEN** the configured portal token env var or control-plane API key env var is not present
- **THEN** `htb check` SHALL report a `FAIL` line naming the missing env var and SHALL not print secret values

#### Scenario: Control-plane key is missing in local onboarding
- **WHEN** the configured control-plane API key is missing during local operator setup
- **THEN** `htb check` SHALL tell the operator to add the key through `/settings/control-plane`, ignored `.htb/secrets.env`, or an environment variable
- **AND** it SHALL NOT imply that the key configures native Worker CLI auth

#### Scenario: Control-plane model is reachable
- **WHEN** required control-plane configuration is present and the provider test succeeds
- **THEN** `htb check` SHALL report `PASS` for the control-plane provider/model connection

#### Scenario: Worker adapter is diagnostic only
- **WHEN** a Worker Adapter is detected but its tracking mode is `observed_only`
- **THEN** `htb check` SHALL report `WARN` that the adapter is diagnostic-only and not normal board-launchable

#### Scenario: Worker adapter is launch-ready
- **WHEN** a Worker Adapter is verified with `proxy_governed` or budget-authoritative `native_usage`
- **THEN** `htb check` SHALL report `PASS` for Worker launch readiness and name the adapter identity separately from the tracking mode

#### Scenario: Support output is safe to paste
- **WHEN** an operator copies `htb check` output into a public support issue
- **THEN** the output SHALL be useful for setup triage without including raw API keys, portal tokens, `.htb/secrets.env` contents, or unredacted credentials

### Requirement: Documentation uses operator setup path
The system SHALL document the operator setup flow as the primary local startup path using the installed `htb` command without requiring sample-data setup, repository-local `uv run htb` commands, or manual secret-file editing for the common portal-driven path.

#### Scenario: Local setup docs avoid export-heavy startup
- **WHEN** an operator reads the local setup or demo runbook
- **THEN** the startup path SHALL prefer installing the CLI, `htb init`, `htb serve`, portal login, `/settings/control-plane` provider/model/API-key entry, explicit control-plane connection test, and `htb check` over a list of unrelated setup exports or repo-local `uv run htb` commands

#### Scenario: Local setup docs preserve secret alternatives
- **WHEN** an operator cannot or does not want to paste a key through the portal
- **THEN** the documentation SHALL describe ignored `.htb/secrets.env` and environment-variable alternatives
- **AND** it SHALL continue to state that `.htb/config.toml` remains non-secret

#### Scenario: Contributor docs keep repo-managed uv commands
- **WHEN** a contributor is working inside the repository checkout
- **THEN** development docs SHALL continue to allow repo-managed commands such as `uv run pytest` and `uv run htb` where appropriate
- **AND** those docs SHALL NOT present `uv run htb` as the primary public operator setup path

### Requirement: Portal edits operator config
The system SHALL persist portal-edited non-secret control-plane connection settings to the operator config file used by local startup.

#### Scenario: Control-plane config saved from portal
- **WHEN** an authenticated operator saves provider, model, base URL, or control-plane API key env name from the portal
- **THEN** the system SHALL write those non-secret settings to `.htb/config.toml`
- **AND** it SHALL preserve unrelated existing operator config values

#### Scenario: API key env name saved
- **WHEN** the operator saves a control-plane API key environment variable name
- **THEN** the system SHALL persist only the environment variable name in `.htb/config.toml`
- **AND** it SHALL NOT persist the API key value in `.htb/config.toml`

### Requirement: Placeholder-only control-plane secret guidance
The system SHALL support portal-managed control-plane API key values for the local operator setup path while continuing to avoid storing raw control-plane API key values in `.htb/config.toml` or exposing them in portal output.

#### Scenario: Env name changes to missing secret entry
- **WHEN** the operator saves a control-plane API key env name that is not present in `.htb/secrets.env`
- **THEN** the system SHALL add a placeholder entry for that env name to `.htb/secrets.env`
- **AND** it SHALL not overwrite any existing secret values

#### Scenario: Env name already has secret entry
- **WHEN** the operator saves a control-plane API key env name already present in `.htb/secrets.env`
- **THEN** the system SHALL preserve the existing value unless the operator submits a non-empty replacement API key value through the authenticated portal form
- **AND** it SHALL not print or expose the existing value

#### Scenario: Portal saves control-plane API key value
- **WHEN** an authenticated local operator submits a non-empty control-plane API key value through the control-plane settings portal
- **THEN** the system SHALL write that value to ignored `.htb/secrets.env` under the configured control-plane API key env name
- **AND** the system SHALL not write the raw key value to `.htb/config.toml`

#### Scenario: Common setup hides env mechanics
- **WHEN** an operator uses the normal control-plane settings portal flow
- **THEN** the system SHALL present provider, model, and API key entry as the primary setup controls
- **AND** the API key env-name field SHALL be hidden, collapsed, or otherwise presented as advanced compatibility configuration rather than a required manual setup step

### Requirement: Effective setting precedence remains visible
The system SHALL preserve existing startup precedence while making portal-edited config behavior understandable to the operator.

#### Scenario: Environment overrides saved config
- **WHEN** an environment variable overrides a portal-saved `.htb/config.toml` control-plane setting
- **THEN** the portal SHALL show or report that the environment value is the effective runtime value
- **AND** the system SHALL NOT silently claim the shadowed config value is active

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

