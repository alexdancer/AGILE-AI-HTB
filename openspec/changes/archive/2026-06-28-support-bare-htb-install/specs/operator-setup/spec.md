## MODIFIED Requirements

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
