## ADDED Requirements

### Requirement: Codex native usage verification
The system SHALL verify Codex in `native_usage` mode when a non-interactive Codex sentinel run emits machine-readable, run-bound token usage evidence for the selected Codex Worker model.

#### Scenario: Codex native verification uses Codex exec JSONL
- **WHEN** the system verifies Codex in `native_usage` mode for an allowed Codex model
- **THEN** the command plan SHALL invoke `codex exec`
- **AND** the command plan SHALL request machine-readable JSONL output with `--json`
- **AND** the command plan SHALL pass the selected Worker model with a Codex-supported model flag
- **AND** the command plan SHALL NOT use OpenCode-specific `run --format json` command shape

#### Scenario: Codex native verification accepts turn completed usage
- **WHEN** Codex verification returns the required sentinel output
- **AND** the JSONL stream includes a run-bound `turn.completed` event with token-complete `usage` evidence for the selected command/model
- **AND** the Codex process exits successfully
- **THEN** the system records adapter verification usage as `adapter_verification`
- **AND** verification evidence records `tracking_mode=native_usage` and `tracking_authoritative=true`
- **AND** the adapter may become launchable for compatible allowed Codex models

#### Scenario: Codex native verification does not require cost
- **WHEN** Codex verification emits token-complete native usage evidence without dollar cost
- **THEN** the system SHALL treat token usage as budget-authoritative
- **AND** the system SHALL record cost as unavailable rather than failing verification solely because cost is absent

#### Scenario: Codex text success without usage is not authoritative
- **WHEN** Codex verification returns the required sentinel output but does not emit trustworthy run-bound usage evidence
- **THEN** the system SHALL NOT record a budget-authoritative adapter verification token row
- **AND** the adapter verification SHALL remain failed or `observed_only`
- **AND** the adapter SHALL NOT become launchable for normal governed Tasks

### Requirement: Verification status reflects tracking authority
The system SHALL distinguish diagnostic observed-only verification from budget-authoritative Worker Adapter verification.

#### Scenario: Observed-only Codex verification is diagnostic
- **WHEN** Codex verification is requested or completed in `observed_only` mode
- **AND** the Codex process returns the required sentinel output
- **THEN** verification evidence SHALL record `tracking_mode=observed_only` and `tracking_authoritative=false`
- **AND** Worker Setup SHALL NOT treat the adapter as normal board-launch-ready

#### Scenario: Native usage request cannot pass with observed-only evidence
- **WHEN** Codex verification is requested in `native_usage` mode
- **AND** only sentinel output or human-readable logs are available
- **THEN** the verification SHALL fail for missing native usage evidence
- **AND** the system SHALL NOT silently downgrade the result into launchable verification
