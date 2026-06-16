## ADDED Requirements

### Requirement: First-class Worker Adapter presets
The system SHALL expose OpenCode, Claude Code, Codex, and Hermes as first-class Worker Adapter presets while allowing only verified adapters to launch.

#### Scenario: Unverified adapter visible but blocked
- **WHEN** a Worker Adapter preset exists but has not passed token-tracking verification
- **THEN** the Portal shows the adapter status and keeps Launch disabled for that adapter

### Requirement: OpenCode first verified adapter
The system SHALL support OpenCode as the first Worker Adapter target for local token-tracking verification.

#### Scenario: OpenCode detected locally
- **WHEN** the Local Runner detects OpenCode is installed and callable
- **THEN** the system shows OpenCode as available for verification but not launchable until sentinel verification passes

### Requirement: Adapter verification sentinel
The system SHALL verify a Worker Adapter by launching the real adapter path with a sentinel prompt routed through the Harness Proxy.

#### Scenario: Sentinel verification passes
- **WHEN** the Worker Adapter responds with the required sentinel output and at least one model call is recorded by the Harness Proxy
- **THEN** the adapter is marked token-tracking verified and launchable for compatible tasks

#### Scenario: Direct proxy call is insufficient
- **WHEN** token usage is recorded without launching the configured Worker Adapter process
- **THEN** the adapter is not marked launchable

### Requirement: Verification usage accounting
The system SHALL record adapter verification model usage as orchestration spend labeled `adapter_verification`.

#### Scenario: Verification tokens are persisted
- **WHEN** adapter verification causes model usage
- **THEN** the token ledger records usage kind `adapter_verification` separate from Worker Session task actuals

### Requirement: Provider keys remain in Harness
The system SHALL keep real provider API keys inside the Harness and provide Workers only a session-scoped Harness key plus Harness Proxy base URL.

#### Scenario: Worker launch environment
- **WHEN** the system launches or verifies a Worker Adapter
- **THEN** the Worker environment contains the Harness Proxy base URL and session-scoped Harness key but not the real provider API key
