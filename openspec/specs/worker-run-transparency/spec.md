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
