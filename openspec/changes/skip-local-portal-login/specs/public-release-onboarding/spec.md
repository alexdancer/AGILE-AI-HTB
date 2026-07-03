## ADDED Requirements

### Requirement: Public onboarding uses direct local Portal entry
The public first-run onboarding path SHALL present no-login loopback access as the default local evaluation path while preserving token guidance for shared access.

#### Scenario: README quickstart opens local Portal directly
- **WHEN** a public operator follows the default local README quickstart
- **THEN** the documented happy path SHALL open `http://localhost:8000/` or the project landing URL directly after `htb serve`
- **AND** it SHALL NOT require portal token entry before first viewing the local Portal

#### Scenario: Public docs preserve shared-access warning
- **WHEN** public docs describe non-loopback, hosted, reverse-proxy, or Docker shared access
- **THEN** they SHALL state that portal token auth is required or must be explicitly considered before exposure
- **AND** they SHALL warn not to paste portal tokens into public support artifacts
