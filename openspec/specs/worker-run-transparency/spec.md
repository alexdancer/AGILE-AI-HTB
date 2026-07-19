# worker-run-transparency Specification

## Purpose
Define how Worker Run timeline events are recorded, redacted, and presented as auditable execution evidence without turning run evidence into operator chat or message-thread semantics.
## Requirements
### Requirement: Worker Run timeline records harness steps
The system SHALL record a chronological, redacted event timeline for each Worker Run.

#### Scenario: Launch records timeline events
- **WHEN** an operator launches a task and a Worker Run is created
- **THEN** the system records timeline events for launch request, launch guardrail result, command planning, adapter start, and final completion or failure
- **AND** each event is linked to the Worker Run

#### Scenario: Timeline distinguishes harness layer
- **WHEN** a timeline event is created
- **THEN** the event identifies whether it describes control-plane/orchestrator activity or Worker/coding harness activity

### Requirement: Worker Run timeline is redacted
The system SHALL redact secrets before persisting Worker Run event details.

#### Scenario: Secret-like detail is omitted or redacted
- **WHEN** an event detail contains an API key, authorization header, password, token, or secret-like value
- **THEN** the persisted event detail omits or redacts the sensitive value

### Requirement: Portal shows Worker Run timeline
The portal SHALL show Worker Run timeline evidence from existing task or session views.

#### Scenario: Operator reviews Worker Run progress
- **WHEN** an operator opens a task or session report for a task with Worker Run evidence
- **THEN** the portal shows the Worker Run events in chronological order
- **AND** the latest failure or retryable event is visible without reading raw stdout or stderr

### Requirement: Timeline avoids message-thread semantics
The system SHALL treat Worker Run timeline entries as execution evidence, not operator chat messages.

#### Scenario: Timeline entry is system-generated
- **WHEN** a Worker Run event appears in the portal
- **THEN** the event is presented as system-generated run evidence
- **AND** the portal does not require reply, unread, or thread behavior for that event

### Requirement: Worker Run timeline records streamed Worker execution activity

The system SHALL record incremental, redacted timeline events derived from the Worker Adapter's
streamed output as the Worker Run executes, in addition to control-plane milestone events. Streamed
events SHALL be normalized to a common vocabulary across adapters — agent message, tool call,
provisional usage, and status — and SHALL be attributed to the Worker/coding-harness layer.

#### Scenario: Streaming adapter output is recorded incrementally

- **WHEN** a Worker Run executes and its adapter emits streamed output lines
- **THEN** the system records normalized timeline events (agent message, tool call, provisional usage, status) as they arrive
- **AND** each event is attributed to the Worker/coding-harness layer and linked to the Worker Run

#### Scenario: Unrecognized stream output does not break the run

- **WHEN** a streamed line cannot be parsed into a known event
- **THEN** the system omits it from the timeline feed
- **AND** the Worker Run continues and completes as it would without streamed capture

#### Scenario: Streamed event details are redacted

- **WHEN** a streamed event's text or tool arguments contain a secret-like value or the launch prompt
- **THEN** the persisted event detail redacts that value before storage

#### Scenario: Streamed events remain evidence, not chat

- **WHEN** a streamed event appears in the portal
- **THEN** it is presented as system-generated run evidence
- **AND** the portal does not provide reply, unread, or thread behavior for the event

### Requirement: Portal presents live Worker Run progress while running

The portal SHALL present the Worker Run timeline live while the run is active, updating without a
manual refresh, and SHALL settle the view when the run completes. Dense post-run evidence views MAY
continue to announce new evidence and require an explicit refresh so reading state stays stable.

#### Scenario: Operator watches a run in progress

- **WHEN** an operator views a task or session whose Worker Run is Running
- **THEN** the portal shows streamed timeline events appearing during the run without a manual refresh

#### Scenario: Live view settles on completion

- **WHEN** the Worker Run completes
- **THEN** the live timeline stops updating and shows the final run evidence

#### Scenario: Dense report keeps stable reading state

- **WHEN** new Worker Run evidence arrives for a session report being read
- **THEN** the report announces fresh evidence and updates on explicit refresh rather than mutating under the reader

### Requirement: Live usage display is provisional until finalized

Any token or usage figure shown while a Worker Run is active SHALL be labeled provisional and SHALL
NOT be presented as the authoritative charge. The authoritative Worker execution token total is the
total finalized when the run completes.

#### Scenario: Provisional live counter is labeled

- **WHEN** a running Worker Run displays an in-progress usage figure
- **THEN** the figure is labeled provisional
- **AND** it is not recorded as the task's actual token total nor charged to the budget

#### Scenario: Finalized total is authoritative

- **WHEN** the Worker Run completes
- **THEN** the authoritative Worker execution token total is derived from the final run evidence
- **AND** it is the value persisted as the task actual and counted against the budget
