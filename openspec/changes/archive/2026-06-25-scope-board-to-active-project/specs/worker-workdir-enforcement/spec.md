## MODIFIED Requirements

### Requirement: Worker launch is bound to connected project root
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
