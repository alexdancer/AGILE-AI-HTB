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
The system SHALL move the task from Running to Review when the Worker Run finishes successfully and required runtime evidence is present.

#### Scenario: Successful worker run enters Review
- **WHEN** a background Worker Run exits with return code 0
- **AND** required token usage evidence for the selected tracking mode is present
- **THEN** the system marks the Worker Run `completed`
- **AND** the associated task moves to Review

### Requirement: Worker Run records review evidence
The system SHALL preserve sanitized Worker Run evidence for operator review after completion, including the configured Worker workdir and evidence of where files were changed when such evidence is available.

#### Scenario: Review evidence is captured
- **WHEN** a Worker Run completes successfully
- **THEN** the system stores sanitized stdout and stderr evidence
- **AND** records session/token evidence
- **AND** records configured workdir and command cwd evidence
- **AND** records git diff, porcelain, or filesystem evidence when the run is associated with a connected project root or configured workdir

#### Scenario: Workdir mismatch prevents completed-work review
- **WHEN** a Worker Run exits successfully
- **AND** the Worker command evidence indicates files were read or edited outside the configured workdir
- **AND** the configured workdir has no expected output or file-change evidence
- **THEN** the system marks the Worker Run failed with workdir mismatch evidence
- **AND** the task returns to Estimated for retry
- **AND** the task card or metadata shows the configured workdir and suspicious outside paths

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
