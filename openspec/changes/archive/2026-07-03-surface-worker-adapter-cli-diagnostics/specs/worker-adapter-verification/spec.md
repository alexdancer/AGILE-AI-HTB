## ADDED Requirements

### Requirement: Verification records sanitized CLI failure summary
Worker Adapter verification SHALL preserve a sanitized user-facing failure summary when the native Worker CLI exits unsuccessfully or emits an error payload that identifies an actionable authentication or configuration prerequisite.

#### Scenario: Claude Code auth failure summary recorded
- **WHEN** Claude Code verification runs in native usage mode
- **AND** the CLI emits JSONL or text evidence equivalent to `Not logged in · Please run /login`
- **AND** the process does not produce trustworthy native usage evidence
- **THEN** verification fails and the adapter remains not launchable
- **AND** verification evidence includes a sanitized user-facing summary identifying the Claude Code login requirement
- **AND** verification evidence does not require the operator to infer the reason from raw JSONL stdout

#### Scenario: CLI failure summary uses redacted evidence
- **WHEN** verification evidence includes stdout, stderr, command plans, environment values, or nested CLI error payloads
- **THEN** any user-facing failure summary is derived only after redaction
- **AND** session API keys, bearer tokens, upstream provider keys, and secret-like values are not displayed
