## MODIFIED Requirements

### Requirement: Blocked failure preservation
The system SHALL preserve evidence when Worker execution cannot complete successfully. Recoverable Worker runtime failures for tasks that were launchable before the attempt SHALL fail the Worker session and preserve sanitized launch evidence without moving the task to the Blocked lifecycle state. Hard safety failures, workflow/dependency blockers, read-only project mutation, write-capable verification failure, budget preflight denial without override, and non-launchable preconditions SHALL remain blocking states.

#### Scenario: Worker session fails recoverably
- **WHEN** OpenCode crashes, exits non-zero, times out, or produces no budget-authoritative token usage for the selected tracking mode after an Estimated or Ready task has been claimed for launch
- **THEN** the system marks the Worker session failed
- **AND** the task returns to its exact pre-launch status
- **AND** the system preserves logs, launch return code, sanitized stderr/stdout, tracking mode, branch name when present, and token ledger entries when present
- **AND** the task remains eligible for a later launch retry

#### Scenario: Safety failure remains blocked
- **WHEN** a Worker launch violates a hard safety guardrail such as read-only project mutation or write-capable verification failure
- **THEN** the Task moves to Blocked and the system preserves logs, token ledger entries when present, failure reason, tracking mode, branch name, and any uncommitted diff without automatic retry

### Requirement: Worker launch model selection
The system SHALL launch Worker Sessions with a model selected from the verified adapter's discovered model inventory unless the User explicitly supplies a compatible override.

#### Scenario: User selects discovered Worker model
- **WHEN** the User launches a task with a model discovered for the selected verified Worker Adapter
- **THEN** the Local Runner passes that model to the Worker Harness launch command and records it on the Worker session

#### Scenario: Selected model is unavailable
- **WHEN** the selected model is not in the selected adapter's discovered model inventory and no explicit compatible override is approved
- **THEN** the system blocks launch and shows the model compatibility reason

## ADDED Requirements

### Requirement: Recoverable launch errors clear on successful retry
The system SHALL overwrite stale recoverable launch-error metadata on each launch attempt and SHALL clear the user-visible launch error after a successful retry.

#### Scenario: Successful retry clears timeout message
- **WHEN** a task has `launch_error` and `last_launch_failure` from a previous Worker timeout
- **AND** the operator launches the task again and the Worker launch succeeds
- **THEN** the task no longer renders the previous timeout as the current launch error
- **AND** the successful session evidence is recorded normally
