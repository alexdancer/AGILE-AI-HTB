## ADDED Requirements

### Requirement: Docker local run documents Portal auth boundary
Docker local run materials SHALL distinguish local published-port convenience from shared/container exposure risk.

#### Scenario: Docker smoke checks Portal reachability without assuming no-auth
- **WHEN** the Docker smoke verification checks the Portal
- **THEN** it SHALL verify a reachable Portal route appropriate to the Docker auth mode
- **AND** it SHALL NOT require no-login behavior unless Docker is explicitly configured for local-only no-auth access

#### Scenario: Docker shared exposure keeps token guidance
- **WHEN** Docker docs describe publishing the Portal port beyond loopback or using Compose defaults that may be reachable from other hosts
- **THEN** they SHALL keep portal token setup guidance
- **AND** they SHALL state that disabling auth is local-only and not safe for shared exposure
