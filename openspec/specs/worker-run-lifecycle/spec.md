# worker-run-lifecycle Specification

## Purpose
Define the persisted Worker Run lifecycle that starts when a launchable task is launched, runs outside the HTTP request lifecycle, records auditable execution evidence, prevents duplicate active launches, and maps completion or retryable operational failures back to task lifecycle states.
## Requirements
### Requirement: Worker Run is persisted when launch starts
The system SHALL create a persisted Worker Run record when a launchable task is launched, before the Worker Adapter command executes.

#### Scenario: Launch creates Worker Run
- **WHEN** an operator launches an Estimated task that passes Launch Guardrails
- **THEN** the system creates a Worker Run linked to the task and session
- **AND** the Worker Run records the selected adapter, selected model, command plan metadata, tracking mode, and initial `running` status

### Requirement: Worker Run executes outside request lifecycle
The system SHALL execute the Worker Adapter command outside the HTTP request lifecycle so the launch response can return before Worker execution completes.

#### Scenario: Launch response returns before worker completion
- **WHEN** a Worker Adapter command is expected to run for multiple minutes
- **AND** the operator clicks Launch from the board
- **THEN** the launch endpoint responds after the Worker Run is created and started
- **AND** the response does not wait for the adapter subprocess to exit

### Requirement: Worker Run success moves task to Review
The system SHALL move the task from Running to Review when the Worker Run finishes successfully and required runtime evidence is present, and SHALL persist the task's actual Worker execution token total from authoritative usage evidence.

#### Scenario: Successful worker run enters Review
- **WHEN** a background Worker Run exits with return code 0
- **AND** required token usage evidence for the selected tracking mode is present
- **THEN** the system marks the Worker Run `completed`
- **AND** the associated task moves to Review
- **AND** the associated task records `actual_tokens` as the Worker execution token total for that completed run's session.

### Requirement: Worker Run records review evidence
The system SHALL preserve sanitized Worker Run evidence for operator review after completion, including the connected project root/effective Worker workdir and evidence of where files were changed when such evidence is available.

#### Scenario: Review evidence is captured
- **WHEN** a Worker Run completes successfully
- **THEN** the system stores sanitized stdout and stderr evidence
- **AND** records session/token evidence
- **AND** records connected project root/effective workdir and command cwd evidence
- **AND** records git diff, porcelain, or filesystem evidence when the run is associated with a connected project root

#### Scenario: Workdir mismatch prevents completed-work review
- **WHEN** a Worker Run exits successfully
- **AND** the Worker command evidence indicates files were read or edited outside the connected project root/effective workdir
- **AND** the connected project root/effective workdir has no expected output or file-change evidence
- **THEN** the system marks the Worker Run failed with workdir mismatch evidence
- **AND** the task returns to Estimated for retry
- **AND** the task card or metadata shows the connected project root/effective workdir and suspicious outside paths

### Requirement: Retryable Worker Run failure returns task to Estimated
The system SHALL return a task to Estimated when a background Worker Run fails due to a retryable operational failure, while preserving enough sanitized command evidence for the operator to diagnose launch command, model, tracking mode, stdout, stderr, and return code.

#### Scenario: Timeout returns to Estimated
- **WHEN** a Running task's Worker Run times out after the adapter command started
- **THEN** the system marks the Worker Run `failed`
- **AND** the task returns to Estimated
- **AND** the task card shows retryable timeout evidence
- **AND** the task remains eligible for another launch

#### Scenario: Nonzero exit returns to Estimated
- **WHEN** a Running task's Worker Run exits nonzero without a hard safety violation
- **THEN** the system marks the Worker Run `failed`
- **AND** the task returns to Estimated with sanitized failure evidence
- **AND** the task remains eligible for another launch

#### Scenario: OpenCode return-code-one failure shows command evidence
- **WHEN** an OpenCode Worker Run exits with return code 1
- **THEN** the task returns to Estimated instead of staying Running
- **AND** the task card or metadata preserves sanitized stderr/stdout and the redacted command plan used for that attempt
- **AND** the preserved evidence includes the selected adapter and selected model

### Requirement: Active Worker Run prevents duplicate launch
The system SHALL prevent a second launch for a task that already has an active Worker Run.

#### Scenario: Duplicate launch rejected
- **WHEN** a task is Running with an active Worker Run
- **AND** the operator submits another Launch request for the same task
- **THEN** the system rejects the duplicate launch or returns the existing active run
- **AND** no second adapter command starts for that task

### Requirement: Worker Run lifecycle includes timeline evidence
The system SHALL include Worker Run timeline events as part of lifecycle evidence for launch, running, review, completion, and retryable operational failure states.

#### Scenario: Failed Worker Run has lifecycle timeline
- **WHEN** a Worker Run fails due to timeout, nonzero adapter exit, missing usage evidence, or workdir mismatch
- **THEN** the Worker Run lifecycle evidence includes timeline events that show the launch attempt, failure class, retryability, and sanitized diagnostic details
- **AND** the associated task remains in the lifecycle state required by the existing Worker Run failure requirements

#### Scenario: Completed Worker Run has review timeline
- **WHEN** a Worker Run completes and moves the task to Review
- **THEN** the Worker Run lifecycle evidence includes timeline events for successful adapter completion and required usage/file evidence capture

### Requirement: Worker Run lifecycle includes repo-context evidence
The system SHALL preserve Repo Context Brief evidence on Worker Runs associated with a connected project.

#### Scenario: Review shows launch context
- **WHEN** an operator reviews a completed Worker Run for a connected project
- **THEN** the lifecycle evidence includes the Repo Context Brief source list and bounded brief content
- **AND** the evidence is available alongside command plan, selected adapter, selected model, tracking mode, and stdout/stderr evidence

### Requirement: Worker Run lifecycle drives queue progression
Worker Run terminal states SHALL be usable as inputs for project board run queue continuation or stop decisions.

#### Scenario: Successful Worker Run advances queue
- **WHEN** a Worker Run launched by a project board queue completes successfully
- **THEN** the task SHALL enter Review through the existing lifecycle
- **AND** the queue SHALL evaluate whether another eligible task can launch

#### Scenario: Retryable Worker Run failure stops queue
- **WHEN** a Worker Run launched by a project board queue fails retryably
- **THEN** the task SHALL return to Estimated with retryable launch evidence
- **AND** the queue SHALL stop instead of launching another task

#### Scenario: Interrupted active run stops queue
- **WHEN** a queued active Worker Run is marked stale or interrupted
- **THEN** the queue SHALL stop with interrupted-run evidence
- **AND** the system SHALL NOT launch the next queue task until an operator restarts automation

### Requirement: Streamed capture preserves accounting and lifecycle transitions

The system SHALL derive the authoritative Worker execution token total and the task lifecycle
transition from the same final run evidence regardless of whether timeline events were captured
incrementally during execution. Incremental streamed capture SHALL NOT alter the final token total
or the lifecycle transition.

#### Scenario: Streamed and non-streamed runs finalize identically

- **WHEN** two Worker Runs produce identical adapter output, one captured incrementally and one not
- **THEN** both persist the same authoritative Worker execution token total
- **AND** both make the same lifecycle transition (Running→Review on success, retryable failure→Estimated)

#### Scenario: Malformed streamed line does not change finalization

- **WHEN** a Worker Run's streamed output contains lines that cannot be parsed as events
- **THEN** the final token total and the lifecycle transition are unchanged from the non-streamed outcome
