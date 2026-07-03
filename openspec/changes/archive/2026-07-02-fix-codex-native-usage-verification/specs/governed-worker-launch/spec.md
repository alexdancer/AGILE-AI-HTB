## ADDED Requirements

### Requirement: Codex native usage launch accounting
The system SHALL launch Codex Worker Sessions in `native_usage` mode through Codex non-interactive JSONL command templates and SHALL record raw cache component evidence and normalized Worker actual usage from Codex `turn.completed.usage` events.

#### Scenario: Codex native launch uses exec JSONL command
- **WHEN** an Estimated Task is launched with the Codex Worker Adapter in `native_usage` mode
- **AND** the selected model is in the Codex adapter's operator-approved allowed model subset
- **THEN** the Local Runner command plan SHALL invoke `codex exec`
- **AND** the command plan SHALL include `--json`
- **AND** the command plan SHALL include the selected allowed Codex Worker model
- **AND** the command plan SHALL include the scoped task prompt
- **AND** the command plan SHALL be recorded with secrets redacted

#### Scenario: Codex native launch records result usage
- **WHEN** a Codex `native_usage` Worker Run exits successfully
- **AND** Codex emits run-bound `turn.completed.usage` evidence
- **THEN** the system records Worker execution usage from the Codex result evidence
- **AND** the recorded raw evidence preserves fresh input, cached input, output, reasoning, provider total, and cost when present
- **AND** normalized Worker actual and budget accounting exclude cache-read/reused-context tokens while preserving them as audit evidence
- **AND** the Worker Run records native usage evidence on the Worker/coding harness layer

#### Scenario: Codex native launch without evidence is recoverable failure
- **WHEN** a Codex `native_usage` Worker Run exits successfully but does not emit trustworthy run-bound usage evidence
- **THEN** the Worker Run SHALL fail with missing native usage evidence
- **AND** the Task SHALL return to Estimated with sanitized retryable launch evidence
- **AND** the Task SHALL NOT be moved to Blocked solely because usage evidence was missing after an otherwise launchable attempt

#### Scenario: Disallowed Codex model is rejected before launch
- **WHEN** a launch request names a Codex model that is not in the Codex adapter's operator-approved allowed model subset
- **THEN** the system SHALL reject the launch before starting any Codex process
- **AND** the rejection SHALL explain that the selected Worker model is not allowed for the adapter
