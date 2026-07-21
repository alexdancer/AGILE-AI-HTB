## MODIFIED Requirements

### Requirement: Blocked failure preservation
The system SHALL preserve evidence when Worker execution cannot complete successfully. Retryable Worker Run failures for tasks that were launchable before the attempt SHALL fail the Worker Run and preserve sanitized evidence without changing the task to a `Blocked` lifecycle status. Hard safety failures, workflow or dependency blockers, read-only project mutation, write-capable verification failure, budget preflight denial without override, and non-launchable preconditions SHALL be represented as a structured Blocked Condition while the task retains its canonical lifecycle status.

#### Scenario: Worker run fails recoverably
- **WHEN** OpenCode crashes, exits non-zero, times out, or produces no budget-authoritative token usage for the selected tracking mode after an Estimated task has been claimed for launch
- **THEN** the system marks the Worker Run and Worker session failed
- **AND** the task returns to Estimated
- **AND** the system preserves logs, launch return code, sanitized stderr/stdout, tracking mode, branch name when present, and token ledger entries when present
- **AND** the task remains eligible for a later launch retry

#### Scenario: Safety failure records a Blocked Condition
- **WHEN** a Worker launch violates a hard safety guardrail such as read-only project mutation or write-capable verification failure
- **THEN** the task retains the canonical lifecycle status it held for that workflow stage
- **AND** the task records a structured Blocked Condition with a sanitized reason, origin, and timestamp
- **AND** the system preserves logs, token ledger entries when present, tracking mode, branch name, and any uncommitted diff without automatic retry

#### Scenario: Successful retry clears resolved launch blocking state
- **WHEN** an operator retries a task after resolving a launch Blocked Condition
- **AND** the Worker launch is accepted
- **THEN** the resolved Blocked Condition and its launch or budget override markers SHALL be removed
- **AND** the task proceeds through Running and Review without displaying the stale blocker
