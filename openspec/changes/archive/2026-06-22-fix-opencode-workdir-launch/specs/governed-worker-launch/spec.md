## MODIFIED Requirements

### Requirement: OpenCode launch uses non-interactive run command
The system SHALL launch OpenCode Worker Sessions through a non-interactive command that includes the `run` subcommand, the configured OpenCode project directory when present, the selected Worker model, JSON output mode, and the scoped task prompt.

#### Scenario: OpenCode launch command includes workdir, model, and prompt
- **WHEN** an Estimated task passes Launch Guardrails for the OpenCode Worker Adapter
- **AND** the selected adapter has a configured workdir
- **THEN** the Local Runner command plan invokes `opencode run`
- **AND** the command plan includes `--dir` with the configured adapter workdir
- **AND** the command plan cwd is the configured adapter workdir
- **AND** the command plan includes `--model` with the selected discovered Worker model
- **AND** the command plan includes the scoped task prompt
- **AND** the command plan is recorded with secrets redacted

#### Scenario: Bare OpenCode template is normalized or rejected
- **WHEN** an existing OpenCode adapter configuration contains a bare launch template equivalent to `opencode`
- **THEN** the system does not launch that bare command for a task run
- **AND** the system either normalizes it to the supported non-interactive run command with the configured workdir or blocks launch with a clear compatibility reason

#### Scenario: Nonzero OpenCode exit preserves useful evidence
- **WHEN** OpenCode exits nonzero after the command plan is launched
- **THEN** the Worker Run is marked failed
- **AND** the task returns to Estimated with retryable launch evidence
- **AND** the task metadata preserves sanitized return code, stdout, stderr, selected adapter, selected model, configured workdir, and command plan
