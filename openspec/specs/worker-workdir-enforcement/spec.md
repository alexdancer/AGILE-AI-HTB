# worker-workdir-enforcement Specification

## Purpose
Define how Worker Adapter launches are bound to their configured working directories and how the harness preserves evidence when Worker output lands somewhere else.

## Requirements

### Requirement: Worker launch is bound to configured workdir
The system SHALL bind Worker Adapter launches to the configured adapter workdir using the adapter's native project-directory mechanism when one exists, and SHALL record the configured workdir in command evidence.

#### Scenario: OpenCode launch passes configured workdir
- **WHEN** the system builds an OpenCode Worker launch command for an adapter with a configured workdir
- **THEN** the command plan invokes `opencode run` with `--dir` set to the configured workdir
- **AND** the command plan cwd is also set to the configured workdir
- **AND** the redacted command plan evidence preserves the configured workdir without exposing secrets

#### Scenario: OpenCode verification passes configured workdir
- **WHEN** the system builds an OpenCode native verification command for an adapter with a configured workdir
- **THEN** the command plan invokes `opencode run` with `--dir` set to the configured workdir
- **AND** the sentinel verification prompt remains the scoped prompt sent to OpenCode

#### Scenario: Custom OpenCode template already specifies dir
- **WHEN** an OpenCode native launch or verification template already includes a `--dir` argument
- **THEN** the system SHALL NOT duplicate the `--dir` argument
- **AND** the launch remains eligible only if the effective workdir matches the configured adapter workdir or a clear compatibility reason is shown

### Requirement: Workdir mismatch evidence is preserved
The system SHALL preserve evidence when a Worker process exits successfully but the resulting work does not appear in the configured workdir.

#### Scenario: Successful process edits outside configured workdir
- **WHEN** a Worker Run exits with return code 0
- **AND** the configured workdir has no expected file changes or output evidence
- **AND** Worker stdout/stderr or parsed native events reference edited files outside the configured workdir
- **THEN** the system records a workdir mismatch failure for the Worker Run
- **AND** the task remains eligible for retry rather than being treated as completed target work
- **AND** the task metadata preserves sanitized configured workdir, command cwd, selected adapter, selected model, and suspicious outside paths

#### Scenario: Successful process writes configured workdir
- **WHEN** a Worker Run exits with return code 0
- **AND** configured-workdir evidence shows files or diffs produced under that workdir
- **THEN** the system may continue the normal Worker Run completion flow
- **AND** the review evidence includes the configured workdir evidence
