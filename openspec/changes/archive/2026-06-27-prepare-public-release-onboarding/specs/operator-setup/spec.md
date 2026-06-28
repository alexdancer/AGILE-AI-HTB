## MODIFIED Requirements

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
The system SHALL document the operator setup flow as the primary local startup path without requiring sample-data setup or manual secret-file editing for the common portal-driven path.

#### Scenario: Local setup docs avoid export-heavy startup
- **WHEN** an operator reads the local setup or demo runbook
- **THEN** the startup path SHALL prefer `htb init`, `htb serve`, portal login, `/settings/control-plane` provider/model/API-key entry, explicit control-plane connection test, and `htb check` over a list of unrelated setup exports

#### Scenario: Local setup docs preserve secret alternatives
- **WHEN** an operator cannot or does not want to paste a key through the portal
- **THEN** the documentation SHALL describe ignored `.htb/secrets.env` and environment-variable alternatives
- **AND** it SHALL continue to state that `.htb/config.toml` remains non-secret
