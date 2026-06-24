## ADDED Requirements

### Requirement: Configurable Task Breakdown Model
The system SHALL provide a separately configurable Task Breakdown Model for Task Breakdown Agent work in the control-plane/orchestrator model layer, distinct from the Estimator LLM and from Worker Adapter models.

#### Scenario: Task Breakdown Model configured
- **WHEN** the operator configures a Task Breakdown Model
- **THEN** AGILE-AI-HTB uses that model for semantic task breakdown and proposed vertical-slice review generation
- **AND** usage is recorded as `task_breakdown` Orchestration Tokens rather than Worker execution spend

#### Scenario: Task Breakdown Model not explicitly configured
- **WHEN** no explicit Task Breakdown Model is configured
- **THEN** the system uses a documented control-plane fallback model setting
- **AND** still labels the usage as Task Breakdown Agent/control-plane spend, not Worker Adapter spend

#### Scenario: Worker Adapter model remains separate
- **WHEN** the Task Breakdown Agent runs before estimation
- **THEN** the system does not use OpenCode, Claude Code, Codex, Hermes, or other Worker Adapter model configuration as the Task Breakdown Model unless explicitly configured as a control-plane model connection
