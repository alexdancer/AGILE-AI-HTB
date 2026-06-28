## MODIFIED Requirements

### Requirement: README first-run onboarding path
The system SHALL provide a public README onboarding path that gets a first-time local operator from install to a tiny governed launch proof without requiring architecture-doc exploration or repository-local `uv run htb` commands.

#### Scenario: Operator follows first-run path
- **WHEN** a public operator reads the README quickstart
- **THEN** the documented happy path SHALL include installing the CLI through a supported public install channel, running `htb init`, running `htb serve`, portal login, `/settings/control-plane` provider/model/API-key entry, explicit control-plane connection test, project connection, Worker Adapter setup, and a tiny launch proof
- **AND** it SHALL identify the portal-managed API key path as the normal local setup path

#### Scenario: First-run path preserves model-layer split
- **WHEN** the README describes control-plane setup and Worker setup
- **THEN** it SHALL state that the control-plane model/API key powers AGILE-AI-HTB estimation, planning, reports, and recommendations
- **AND** it SHALL state that native OpenCode, Claude Code, Codex, Hermes, or other Worker CLI auth remains configured in those tools or their adapter setup

#### Scenario: Contributor workflow remains available
- **WHEN** a contributor reads development or test instructions
- **THEN** the documentation SHALL keep repo-local commands such as `uv run pytest` and MAY mention `uv run htb` as a contributor workflow
- **AND** it SHALL distinguish that from the public operator install path that uses bare `htb` commands
