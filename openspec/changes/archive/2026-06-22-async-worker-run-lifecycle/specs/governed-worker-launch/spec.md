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

### Requirement: Worker Adapter tracking modes
The system SHALL treat Worker Adapters as local coding-agent CLI integrations and SHALL separately verify how token usage is proven for each adapter launch.

#### Scenario: Adapter launchability depends on tracking mode
- **WHEN** a Worker Adapter for OpenCode, Claude Code, Codex, Hermes, or a custom command is configured
- **THEN** the system records its tracking mode as `proxy_governed`, `native_usage`, or `observed_only`
- **AND** `proxy_governed` adapters are launchable for governed Tasks only after Harness Proxy token rows are verified
- **AND** `native_usage` adapters are launchable for governed Tasks only after trustworthy CLI usage evidence is verified and recorded
- **AND** `observed_only` adapters are not launchable for governed Tasks

#### Scenario: Native usage evidence is trustworthy
- **WHEN** a Worker Adapter is verified in `native_usage` mode
- **THEN** the emitted usage evidence includes the selected model, prompt or input tokens, completion or output tokens, total tokens, exit status, and command/session identity or equivalent evidence binding the usage to the launched Worker Run
- **AND** the evidence is machine-readable rather than scraped only from human-readable logs

#### Scenario: Weak native usage remains observed only
- **WHEN** a Worker Adapter emits approximate usage, human-readable-only logs, missing model identity, or usage that cannot be bound to the launched Worker Run
- **THEN** the adapter is treated as `observed_only`
- **AND** the adapter is not launchable for governed Tasks

#### Scenario: Tracking mode determines runtime governance
- **WHEN** a Worker Run uses `proxy_governed` tracking mode
- **THEN** runtime request guardrails may apply while Worker model calls pass through the Harness Proxy
- **WHEN** a Worker Run uses `native_usage` tracking mode
- **THEN** the run is budget-authoritative only through launch/review governance, preflight budget checks, post-run reconciliation, evidence review, and alarms after usage is known
- **AND** the system SHALL NOT label `native_usage` as runtime request-governed

#### Scenario: Native usage budget override is explicit
- **WHEN** a Task estimate exceeds the remaining daily Worker budget
- **AND** the selected Worker Adapter uses `native_usage` tracking mode
- **THEN** the Portal MAY allow Launch with budget override
- **AND** the operator must acknowledge that native usage cannot be request-throttled mid-run
- **AND** the Worker Run records the budget override approval for audit
- **AND** post-run reconciliation may report an overrun after native usage evidence is imported

#### Scenario: Portal labels tracking strength explicitly
- **WHEN** the Portal renders Worker Adapter tracking mode
- **THEN** `proxy_governed` is labeled `Governed via Harness Proxy`
- **AND** `native_usage` is labeled `Tracked via Native Usage`
- **AND** `observed_only` is labeled `Observed Only`
- **AND** the Portal shows launch readiness separately from runtime request guardrail availability and accounting authority
- **AND** the Portal SHALL NOT use a generic `Governed` label for all launchable adapters

#### Scenario: Observed-only runs are diagnostic only
- **WHEN** a Worker Adapter has `observed_only` tracking mode
- **THEN** the normal AGILE Board SHALL NOT launch it for a Task
- **AND** Worker Setup MAY provide a separate diagnostic action that records command start evidence, stdout/stderr, exit code or timeout, detected model when available, and a not-budget-authoritative warning
- **AND** the diagnostic action SHALL NOT change task state, show a Launch-ready badge, or present the run as a governed Worker Session

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
