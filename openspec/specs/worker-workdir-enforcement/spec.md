# worker-workdir-enforcement Specification

## Purpose
Define how Worker Adapter launches are bound to the task-bound connected project root and how the harness preserves evidence when Worker output lands somewhere else.

## Requirements

### Requirement: Worker launch is bound to task-selected connected project root
The system SHALL bind normal Worker Adapter launches to the task's selected connected project root using the adapter's native project-directory mechanism when one exists, and SHALL record the effective project id/root/workdir in command evidence. The system SHALL NOT fall back from an unbound or mismatched task to a different most-recent connected project root.

#### Scenario: OpenCode launch passes connected project root
- **WHEN** the system builds an OpenCode Worker launch command for a task-bound connected project root
- **THEN** the command plan invokes `opencode run` with `--dir` set to the task-bound project root
- **AND** the command plan cwd is also set to the task-bound project root
- **AND** the redacted command plan evidence preserves the effective project root/workdir without exposing secrets

#### Scenario: OpenCode verification remains project independent
- **WHEN** the system builds an OpenCode native verification command
- **THEN** verification may run without requiring a task-bound project root
- **AND** the sentinel verification prompt remains the scoped prompt sent to OpenCode

#### Scenario: Custom OpenCode launch template already specifies dir
- **WHEN** an OpenCode native launch template already includes a `--dir` argument
- **THEN** the system SHALL NOT duplicate the `--dir` argument
- **AND** the launch command SHALL bind that argument to the task-bound connected project root

#### Scenario: Unbound task does not use most recent project fallback
- **WHEN** a normal Worker launch is requested for a task without valid connected project binding
- **AND** one or more connected projects exist
- **THEN** the system SHALL reject the launch before starting any Worker Adapter process
- **AND** the system SHALL NOT use the most recently updated connected project root as an implicit fallback

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
