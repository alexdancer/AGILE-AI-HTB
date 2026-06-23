# worker-adapter-verification Specification

## Purpose
Define Worker Adapter presets and token-tracking verification rules so local agent adapters become launchable only after real budget-authoritative usage is proven without exposing control-plane provider credentials to Worker Harnesses.

## Requirements

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
The system SHALL verify a Worker Adapter by launching the real adapter path with a sentinel prompt and proving token usage through a declared tracking mode. Verification SHALL record tracking mode, tracking authority, selected model, usage evidence source, and sanitized command evidence.

#### Scenario: Proxy-governed sentinel verification passes
- **WHEN** the Worker Adapter responds with the required sentinel output through the Harness Proxy and at least one model call is recorded by the Harness Proxy
- **THEN** the adapter is marked proxy-governed verified and launchable for compatible tasks
- **AND** verification evidence records `tracking_mode=proxy_governed` and `tracking_authoritative=true`

#### Scenario: Native usage sentinel verification passes
- **WHEN** the Worker Adapter responds with the required sentinel output using native harness configuration and the Local Runner imports trustworthy usage evidence for that Worker session
- **THEN** the adapter is marked native-usage verified and launchable for compatible tasks
- **AND** verification evidence records `tracking_mode=native_usage` and `tracking_authoritative=true`

#### Scenario: Direct proxy call is insufficient
- **WHEN** token usage is recorded without launching the configured Worker Adapter process
- **THEN** the adapter is not marked launchable

#### Scenario: Observed-only launch is insufficient for governed launch
- **WHEN** the Worker Adapter can be launched but no budget-authoritative proxy or native usage evidence is available
- **THEN** the adapter may be marked observed-only but is not eligible for normal governed launch
- **AND** verification evidence records `tracking_mode=observed_only` and `tracking_authoritative=false`

### Requirement: Verification usage accounting
The system SHALL record adapter verification model usage as orchestration spend labeled `adapter_verification` and include the verified tracking mode when known.

#### Scenario: Verification tokens are persisted
- **WHEN** adapter verification causes model usage
- **THEN** the token ledger records usage kind `adapter_verification` separate from Worker Session task actuals

#### Scenario: Native verification usage imported
- **WHEN** adapter verification uses native Worker Harness usage import
- **THEN** the token ledger records the imported usage with source metadata identifying the Worker Harness and native tracking mode

### Requirement: Provider keys remain separated from Worker Harness native config
The system SHALL keep AGILE-AI-HTB control-plane provider credentials separate from Worker Harness native credentials, SHALL only inject Harness Proxy credentials into Workers for proxy-governed tracking mode, and SHALL NOT expose real upstream provider API keys to Worker Adapter processes unless explicitly required by that Worker Harness's native configuration outside AGILE-AI-HTB.

#### Scenario: Proxy-governed Worker launch environment
- **WHEN** the system launches or verifies a Worker Adapter in proxy-governed mode
- **THEN** the Worker environment contains the Harness Proxy base URL and session-scoped Harness key but not the real control-plane provider API key

#### Scenario: Native Worker launch environment
- **WHEN** the system launches or verifies a Worker Adapter in native usage mode
- **THEN** the Worker uses its native harness configuration and the system does not require a control-plane provider key, Harness Proxy URL, or session API key as Worker Harness auth

#### Scenario: Direct provider clients used upstream
- **WHEN** a proxy-governed Worker call reaches AGILE-AI-HTB's Harness Proxy
- **THEN** AGILE-AI-HTB forwards the governed request upstream through its configured direct provider client without passing the upstream provider key to the Worker Adapter process

### Requirement: Native usage evidence must be trustworthy
The system SHALL treat native Worker usage as budget-authoritative only when the evidence is machine-readable, token-complete, model-aware, exit-status-aware, and bound to the launched Worker Run.

#### Scenario: Native usage evidence passes authority checks
- **WHEN** native usage evidence includes selected model, prompt or input tokens, completion or output tokens, total tokens, exit status, and command/session identity or equivalent run-binding evidence
- **THEN** the system may mark the adapter verification as `native_usage` and budget-authoritative

#### Scenario: Weak native evidence falls back to observed only
- **WHEN** native usage evidence is approximate, human-readable-only, missing model identity, missing token totals, missing exit status, or cannot be bound to the launched Worker Run
- **THEN** the system treats the adapter as `observed_only`
- **AND** the adapter is not eligible for normal governed launch
