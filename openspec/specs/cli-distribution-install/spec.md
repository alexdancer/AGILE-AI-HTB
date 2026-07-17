# cli-distribution-install Specification

## Purpose
TBD - created by archiving change support-bare-foremanctl-install. Update Purpose after archive.
## Requirements
### Requirement: Installed CLI exposes bare foremanctl command
The system SHALL provide supported install paths that make the `foremanctl` command available on the operator's `PATH` without requiring `uv run` from a repository checkout.

#### Scenario: pipx installs released package
- **WHEN** an operator installs Foreman AI HQ with `pipx install foreman-ai-hq`
- **THEN** the installed environment SHALL expose an `foremanctl` command on `PATH`
- **AND** `foremanctl --help` SHALL show the Foreman AI HQ operator command usage

#### Scenario: pipx installs from GitHub before package release
- **WHEN** an operator installs Foreman AI HQ from the GitHub source URL with `pipx`
- **THEN** the installed environment SHALL expose the same `foremanctl` command on `PATH`
- **AND** the documented next command SHALL be `foremanctl init`

#### Scenario: Installed command runs operator setup
- **WHEN** the installed `foremanctl` command is available on `PATH`
- **THEN** `foremanctl init`, `foremanctl serve`, and `foremanctl check` SHALL invoke the existing operator CLI entrypoint without requiring a repository-local `uv run` prefix

### Requirement: Curl installer bootstraps isolated CLI install
The system SHALL provide a shell installer that installs Foreman AI HQ through an isolated Python CLI installer and verifies that `foremanctl` is callable.

#### Scenario: Installer uses available uv tool
- **WHEN** the curl installer runs on a system with `uv` available
- **THEN** it SHALL install Foreman AI HQ as a uv tool or equivalent isolated command install
- **AND** it SHALL verify `command -v foremanctl` before reporting success

#### Scenario: Installer falls back to pipx
- **WHEN** the curl installer runs on a system without `uv` but with `pipx` available
- **THEN** it SHALL install Foreman AI HQ with `pipx`
- **AND** it SHALL verify `command -v foremanctl` before reporting success

#### Scenario: Installer reports missing prerequisites
- **WHEN** the curl installer cannot find a supported installer or cannot make `foremanctl` visible on `PATH`
- **THEN** it SHALL exit nonzero with concise remediation guidance such as installing `uv` or `pipx`, running `pipx ensurepath`, or running `uv tool update-shell`
- **AND** it SHALL NOT prompt for or handle API keys, portal tokens, or other secrets

### Requirement: Homebrew install path is documented truthfully
The system SHALL provide Homebrew installation guidance or scaffolding that makes the availability state of the tap/formula explicit.

#### Scenario: Homebrew formula is available
- **WHEN** a Homebrew tap/formula has been published for Foreman AI HQ
- **THEN** public docs SHALL show the validated `brew` install command and the next operator command `foremanctl init`

#### Scenario: Homebrew formula is not yet published
- **WHEN** the Homebrew tap/formula is only planned or scaffolded
- **THEN** public docs SHALL NOT imply that `brew install` is live
- **AND** they SHALL direct operators to the validated `pipx` or curl installer path instead

### Requirement: Distribution does not bundle Worker Adapter auth
The install channels SHALL install the Foreman AI HQ operator CLI only and SHALL preserve the existing model/auth boundary between Control Plane setup and native Worker Adapter setup.

#### Scenario: Operator installs Foreman AI HQ CLI
- **WHEN** an operator installs Foreman AI HQ through `pipx`, curl installer, or Homebrew
- **THEN** the installer SHALL NOT require OpenCode, Claude Code, Codex, Hermes, provider API keys, portal tokens, or Worker credentials
- **AND** Worker Adapter setup SHALL remain a separate post-login Portal flow

