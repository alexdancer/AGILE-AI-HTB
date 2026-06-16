## MODIFIED Requirements

### Requirement: First-class Worker Adapter presets
The system SHALL expose OpenCode, Claude Code, Codex, and Hermes as first-class Worker Adapter presets while allowing only adapters with verified budget-authoritative tracking modes to launch normal governed tasks.

#### Scenario: Unverified adapter visible but blocked
- **WHEN** a Worker Adapter preset exists but has not passed token-tracking verification
- **THEN** the Portal shows the adapter status and keeps normal governed Launch disabled for that adapter

#### Scenario: Adapter verified in native usage mode
- **WHEN** a Worker Adapter has proven native usage import for at least one discovered model
- **THEN** the Portal shows the adapter as native-usage verified and eligible for governed local launch with compatible discovered models

### Requirement: OpenCode first verified adapter
The system SHALL support OpenCode as the first Worker Adapter target for local token-tracking verification through either proxy-governed mode or native usage mode.

#### Scenario: OpenCode detected locally
- **WHEN** the Local Runner detects OpenCode is installed and callable
- **THEN** the system shows OpenCode as available for model discovery and verification but not launchable until a tracking mode passes verification

#### Scenario: OpenCode native usage verified
- **WHEN** the Local Runner launches OpenCode natively and imports trustworthy per-session model usage evidence
- **THEN** the system marks OpenCode as native-usage verified for the discovered model used by that verification

### Requirement: Adapter verification sentinel
The system SHALL verify a Worker Adapter by launching the real adapter path with a sentinel prompt and proving token usage through a declared tracking mode.

#### Scenario: Proxy-governed sentinel verification passes
- **WHEN** the Worker Adapter responds with the required sentinel output through the Harness Proxy and at least one model call is recorded by the Harness Proxy
- **THEN** the adapter is marked proxy-governed verified and launchable for compatible tasks

#### Scenario: Native usage sentinel verification passes
- **WHEN** the Worker Adapter responds with the required sentinel output using native harness configuration and the Local Runner imports trustworthy usage evidence for that Worker session
- **THEN** the adapter is marked native-usage verified and launchable for compatible tasks

#### Scenario: Direct proxy call is insufficient
- **WHEN** token usage is recorded without launching the configured Worker Adapter process
- **THEN** the adapter is not marked launchable

#### Scenario: Observed-only launch is insufficient for governed launch
- **WHEN** the Worker Adapter can be launched but no budget-authoritative proxy or native usage evidence is available
- **THEN** the adapter may be marked observed-only but is not eligible for normal governed launch

### Requirement: Verification usage accounting
The system SHALL record adapter verification model usage as orchestration spend labeled `adapter_verification` and include the verified tracking mode when known.

#### Scenario: Verification tokens are persisted
- **WHEN** adapter verification causes model usage
- **THEN** the token ledger records usage kind `adapter_verification` separate from Worker Session task actuals

#### Scenario: Native verification usage imported
- **WHEN** adapter verification uses native Worker Harness usage import
- **THEN** the token ledger records the imported usage with source metadata identifying the Worker Harness and native tracking mode

### Requirement: Provider keys remain separated from Worker Harness native config
The system SHALL keep AGILE-AI-HTB control-plane provider credentials separate from Worker Harness native credentials and SHALL only inject Harness Proxy credentials into Workers for proxy-governed tracking mode.

#### Scenario: Proxy-governed Worker launch environment
- **WHEN** the system launches or verifies a Worker Adapter in proxy-governed mode
- **THEN** the Worker environment contains the Harness Proxy base URL and session-scoped Harness key but not the real control-plane provider API key

#### Scenario: Native Worker launch environment
- **WHEN** the system launches or verifies a Worker Adapter in native usage mode
- **THEN** the Worker uses its native harness configuration and the system does not require a control-plane provider key as Worker Harness auth
