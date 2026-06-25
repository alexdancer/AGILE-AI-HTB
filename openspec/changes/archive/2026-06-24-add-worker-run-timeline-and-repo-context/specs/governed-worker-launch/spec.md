## ADDED Requirements

### Requirement: Governed Worker launch includes Repo Context Brief
The system SHALL include the Repo Context Brief in the Worker launch prompt for connected-project governed Worker Runs before task-specific instructions.

#### Scenario: Launch prompt includes repo context
- **WHEN** an Estimated task for a connected project passes Launch Guardrails
- **AND** the system builds a Repo Context Brief
- **THEN** the Worker Adapter command prompt includes the brief before the task description
- **AND** the prompt tells the Worker to inspect existing relevant files before editing

### Requirement: Governed Worker launch records repo-context event
The system SHALL record Worker Run timeline events for Repo Context Brief creation during governed Worker launch.

#### Scenario: Repo context event is recorded
- **WHEN** the system builds and injects a Repo Context Brief for a governed Worker Run
- **THEN** the Worker Run timeline records a repo-context event with sanitized source names and bounded detail

### Requirement: Governed Worker launch preserves model-layer separation in events
The system SHALL label launch events so operators can distinguish control-plane/orchestrator decisions from Worker/coding harness execution.

#### Scenario: Operator reads launch timeline
- **WHEN** an operator views a governed Worker Run timeline
- **THEN** guardrail, repo-context, and prompt-construction events are labeled as control-plane/orchestrator activity
- **AND** adapter subprocess, native/proxy usage, and file evidence events are labeled as Worker/coding harness activity
