## ADDED Requirements

### Requirement: Local loopback setup avoids mandatory portal login
The operator setup flow SHALL treat portal-token login as shared-access protection rather than a required step for default loopback local startup.

#### Scenario: Default local serve prints direct Portal URL
- **WHEN** an operator runs `htb init` and then starts the default local server
- **THEN** setup guidance SHALL direct the operator to open the Portal landing URL such as `http://localhost:8000/`
- **AND** it SHALL NOT require copying the portal token before viewing the local Portal

#### Scenario: Check does not fail local loopback on missing portal token
- **WHEN** auth is not required for the effective local loopback Portal configuration
- **THEN** `htb check` SHALL NOT fail readiness solely because the portal token value is missing
- **AND** it SHALL still avoid printing raw token values when a token exists

#### Scenario: Shared access guidance keeps token setup
- **WHEN** operator setup output or docs describe binding to `0.0.0.0`, Docker shared exposure, hosted access, or explicitly auth-required mode
- **THEN** they SHALL state that portal token auth is required
- **AND** they SHALL point to ignored `.htb/secrets.env` or the configured portal token environment variable without printing the token value
