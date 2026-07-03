## ADDED Requirements

### Requirement: Worker Run preserves actionable native CLI failure summary
Governed Worker launch SHALL preserve a sanitized user-facing failure summary when a native Worker CLI exits before useful work because of an actionable local CLI prerequisite, while preserving the existing retryable Worker Run failure behavior.

#### Scenario: Native CLI prerequisite failure remains retryable
- **WHEN** a Worker Run starts for an Estimated task
- **AND** the native Worker CLI exits nonzero because of an actionable local prerequisite such as missing login, project trust, or local CLI configuration
- **THEN** the Worker Run is marked failed with retryable failure metadata
- **AND** the task returns to Estimated rather than Blocked unless an independent hard safety guardrail applies
- **AND** the task metadata preserves a sanitized user-facing failure summary, return code, selected adapter, selected model, tracking mode, and project root when available

#### Scenario: CLI failure summary does not change tracking authority
- **WHEN** a native Worker CLI prerequisite failure is preserved for a Worker Run
- **THEN** the failure summary does not mark the adapter as verified, unverified, proxy-governed, native-usage-authoritative, or observed-only by itself
- **AND** tracking authority continues to come from the existing verification and usage-evidence rules
