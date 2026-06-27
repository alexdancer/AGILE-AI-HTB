## ADDED Requirements

### Requirement: Claude Code native usage launch accounting
The system SHALL launch Claude Code Worker Sessions in `native_usage` mode through non-interactive Claude Code command templates and SHALL record cache-inclusive token usage and actual cost from Claude Code result JSON.

#### Scenario: Claude Code native launch records result usage
- **WHEN** an Estimated Task is launched with the Claude Code Worker Adapter in `native_usage` mode
- **AND** Claude Code exits successfully and emits result JSON containing `session_id`, `usage`, `modelUsage`, and `total_cost_usd`
- **THEN** the system records Worker execution usage from the Claude Code result evidence
- **AND** the recorded prompt-side tokens include `input_tokens`, `cache_creation_input_tokens`, and `cache_read_input_tokens`
- **AND** the recorded completion tokens include `output_tokens`
- **AND** the recorded cost uses `total_cost_usd` or matching `modelUsage` cost evidence
- **AND** the Worker Run records native usage evidence on the Worker/coding harness layer

#### Scenario: Claude Code native launch without evidence is recoverable failure
- **WHEN** a Claude Code `native_usage` Worker Run exits successfully but does not emit trustworthy usage and cost evidence
- **THEN** the Worker Run SHALL fail with missing native usage evidence
- **AND** the Task SHALL return to Estimated with sanitized retryable launch evidence
- **AND** the Task SHALL NOT be moved to Blocked solely because usage evidence was missing after an otherwise launchable attempt

#### Scenario: Claude Code native launch does not claim runtime request governance
- **WHEN** a Worker Run uses Claude Code with `native_usage` tracking mode
- **THEN** the Portal and Worker Run evidence SHALL present the run as budget-authoritative after native usage import
- **AND** the system SHALL NOT label it as runtime request-governed by the Harness Proxy
