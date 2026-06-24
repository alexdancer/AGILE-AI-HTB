# worker-workdir-enforcement Specification

## Purpose
Define how Worker Adapter launches are bound to the active connected project root and how the harness preserves evidence when Worker output lands somewhere else.

## Requirements

### Requirement: Worker launch is bound to connected project root
The system SHALL bind normal Worker Adapter launches to the connected project root using the adapter's native project-directory mechanism when one exists, and SHALL record the effective project root/workdir in command evidence.

#### Scenario: OpenCode launch passes connected project root
- **WHEN** the system builds an OpenCode Worker launch command for an active project root
- **THEN** the command plan invokes `opencode run` with `--dir` set to the active project root
- **AND** the command plan cwd is also set to the active project root
- **AND** the redacted command plan evidence preserves the configured workdir/project root without exposing secrets

#### Scenario: OpenCode verification remains project independent
- **WHEN** the system builds an OpenCode native verification command
- **THEN** verification may run without requiring an active project root
- **AND** the sentinel verification prompt remains the scoped prompt sent to OpenCode

#### Scenario: Custom OpenCode launch template already specifies dir
- **WHEN** an OpenCode native launch template already includes a `--dir` argument
- **THEN** the system SHALL NOT duplicate the `--dir` argument
- **AND** the launch command SHALL bind that argument to the active connected project root

### Requirement: Workdir mismatch evidence is preserved
The system SHALL preserve evidence when a Worker process exits successfully but the resulting work does not appear in the connected project root/workdir.

#### Scenario: Successful process edits outside project root
- **WHEN** a Worker Run exits with return code 0
- **AND** the connected project root has no expected file changes or output evidence
- **AND** Worker stdout/stderr or parsed native events reference edited files outside the connected project root
- **THEN** the system records a workdir mismatch failure for the Worker Run
- **AND** the task remains eligible for retry rather than being treated as completed target work
- **AND** the task metadata preserves sanitized project root/workdir, command cwd, selected adapter, selected model, and suspicious outside paths

#### Scenario: Successful process writes connected project root
- **WHEN** a Worker Run exits with return code 0
- **AND** project-root/workdir evidence shows files or diffs produced under that root
- **THEN** the system may continue the normal Worker Run completion flow
- **AND** the review evidence includes the project-root/workdir evidence
