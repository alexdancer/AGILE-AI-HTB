## MODIFIED Requirements

### Requirement: Blocked failure preservation
The system SHALL preserve evidence when Worker execution cannot complete successfully. Retryable Worker Run failures for tasks that were launchable before the attempt SHALL fail the Worker Run and preserve sanitized evidence without moving the task to the Blocked lifecycle state. Hard safety failures, workflow/dependency blockers, read-only project mutation, write-capable verification failure, budget preflight denial without override, and non-launchable preconditions SHALL remain blocking states.

#### Scenario: Worker run fails recoverably
- **WHEN** OpenCode crashes, exits non-zero, times out, or produces no budget-authoritative token usage for the selected tracking mode after an Estimated task has been claimed for launch
- **THEN** the system marks the Worker Run and Worker session failed
- **AND** the task returns to Estimated
- **AND** the system preserves logs, launch return code, sanitized stderr/stdout, tracking mode, branch name when present, and token ledger entries when present
- **AND** the task remains eligible for a later launch retry

#### Scenario: Safety failure remains blocked
- **WHEN** a Worker launch violates a hard safety guardrail such as read-only project mutation or write-capable verification failure
- **THEN** the Task moves to Blocked and the system preserves logs, token ledger entries when present, failure reason, tracking mode, branch name, and any uncommitted diff without automatic retry

### Requirement: Recoverable launch errors clear on successful retry
The system SHALL overwrite stale recoverable launch-error metadata on each launch attempt and SHALL clear the user-visible launch error after a successful retry or successful Worker Run completion.

#### Scenario: Successful retry clears timeout message
- **WHEN** a task has `launch_error` and `last_launch_failure` from a previous Worker timeout
- **AND** the operator launches the task again and the Worker Run starts successfully
- **THEN** the task no longer renders the previous timeout as the current launch error
- **AND** the successful session evidence is recorded normally when the Worker Run completes

## ADDED Requirements

### Requirement: Launch starts asynchronous Worker Run
The system SHALL treat Launch as the start of a governed asynchronous Worker Run rather than completion of the entire Worker Adapter command.

#### Scenario: Launch returns while worker command continues
- **WHEN** an Estimated task passes Launch Guardrails
- **AND** the selected Worker Adapter command starts successfully
- **THEN** the task moves to Running
- **AND** the launch response returns before the Worker Adapter command exits
- **AND** the command continues under the associated Worker Run

### Requirement: Worker completion enters Review
The system SHALL transition successful governed Worker execution into Review instead of leaving standard launches indefinitely in Running.

#### Scenario: Standard worker run completes
- **WHEN** a standard Worker Run exits successfully
- **AND** required tracking evidence is present
- **THEN** the task moves from Running to Review
- **AND** the task retains its session association and run evidence
