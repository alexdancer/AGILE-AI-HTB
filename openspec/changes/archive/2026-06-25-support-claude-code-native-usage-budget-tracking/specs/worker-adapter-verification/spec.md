## ADDED Requirements

### Requirement: Claude Code native usage verification
The system SHALL verify Claude Code in `native_usage` mode when a non-interactive Claude Code sentinel run emits machine-readable, run-bound token usage and cost evidence for the selected Worker model.

#### Scenario: Claude Code native verification records cache-inclusive usage
- **WHEN** Claude Code verification runs with `claude -p --model {model} --output-format json|stream-json --verbose` and returns the required sentinel output
- **AND** the result evidence includes `session_id`, `usage`, `modelUsage`, and `total_cost_usd`
- **THEN** the system records adapter verification usage as `adapter_verification`
- **AND** the recorded prompt-side tokens include `input_tokens`, `cache_creation_input_tokens`, and `cache_read_input_tokens`
- **AND** the recorded completion tokens include `output_tokens`
- **AND** verification evidence records `tracking_mode=native_usage` and `tracking_authoritative=true`

#### Scenario: Claude Code text success without usage is not authoritative
- **WHEN** Claude Code verification returns the required sentinel output but does not emit trustworthy run-bound usage and cost evidence
- **THEN** the system SHALL NOT record a budget-authoritative adapter verification token row
- **AND** the adapter verification SHALL remain failed or `observed_only`
- **AND** the adapter SHALL NOT become launchable for normal governed Tasks

#### Scenario: Claude Code native verification uses native auth only
- **WHEN** the system verifies Claude Code in `native_usage` mode
- **THEN** the command SHALL use Claude Code's native configuration and OAuth/auth state
- **AND** the command SHALL NOT require Harness Proxy URL, Harness session API key, or AGILE-AI-HTB control-plane provider credentials
