## ADDED Requirements

### Requirement: In-process background Worker Run executor
The local execution backend SHALL provide an in-process background executor that can run Worker Adapter command plans after the launch response returns.

#### Scenario: Local runner starts background execution
- **WHEN** the local Control Plane starts a Worker Run for a launchable task
- **THEN** the local execution backend schedules the adapter command on an in-process background executor
- **AND** the HTTP launch response is not tied to adapter command completion

### Requirement: Worker Run state survives navigation
The local execution backend SHALL persist Worker Run state in SQLite so operators can navigate away from and back to the board while execution continues.

#### Scenario: Operator leaves board during run
- **WHEN** an operator launches a task and navigates to another portal page
- **AND** the Worker Adapter command is still running
- **THEN** returning to the board shows the task as Running based on persisted Worker Run state

### Requirement: Stale active runs are recoverable
The local execution backend SHALL surface stale active Worker Runs as retryable operational failures when the in-process executor can no longer prove the run is active.

#### Scenario: Web process restarts during run
- **WHEN** the web process restarts while a Worker Run was recorded as running
- **AND** no active executor owns that run after startup
- **THEN** the system marks or surfaces the Worker Run as interrupted
- **AND** the task returns to Estimated with retryable interrupted-run evidence
