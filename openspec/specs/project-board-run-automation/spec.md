# project-board-run-automation Specification

## Purpose
Define bounded project-board run automation that can refresh active Worker Runs, launch eligible project tasks one at a time, optionally request advisory Agent Review, and stop before manual, safety, setup, or budget decisions are required.

## Requirements

### Requirement: Project board exposes run automation controls
The selected project board SHALL expose bounded run automation controls for eligible Estimated tasks in that project.

#### Scenario: Project board shows automation summary
- **WHEN** an authenticated operator opens `/projects/{project_id}/board`
- **THEN** the board SHALL show counts for Estimated tasks eligible for automation, active Running tasks, and tasks awaiting Review
- **AND** the board SHALL describe the automation policy as project-scoped and one-at-a-time

#### Scenario: Run automation controls are project-scoped
- **WHEN** an authenticated operator opens `/projects/{project_id}/board`
- **THEN** the board SHALL offer `Run next task` and `Run queue` controls for that project
- **AND** those controls SHALL include the selected project id in the request

#### Scenario: Global board does not start an ambiguous queue
- **WHEN** an authenticated operator opens the global `/board` view without a selected project
- **THEN** the system SHALL NOT start a run queue without an explicit project selection

### Requirement: Run next launches one eligible project task
The system SHALL provide a `Run next task` action that launches exactly one eligible Estimated task from the selected project board.

#### Scenario: Run next starts one task
- **WHEN** an authenticated operator requests `Run next task` from `/projects/{project_id}/board`
- **AND** at least one Estimated task is bound to `{project_id}` and passes launch guardrails
- **THEN** the system SHALL launch one task through the existing Worker Run lifecycle
- **AND** the task SHALL move to Running with automation metadata recording `run_next`

#### Scenario: Run next has no eligible task
- **WHEN** an authenticated operator requests `Run next task`
- **AND** no Estimated task in the selected project is eligible for launch
- **THEN** the system SHALL leave task state unchanged
- **AND** the board SHALL show a no-eligible-task message

### Requirement: Run queue launches eligible tasks one at a time
The system SHALL provide a `Run queue` action that launches eligible Estimated tasks for the selected project one at a time until a stop condition is reached.

#### Scenario: Queue starts first eligible task
- **WHEN** an authenticated operator starts the run queue from `/projects/{project_id}/board`
- **AND** an eligible Estimated task exists for that project
- **THEN** the system SHALL launch the first eligible task
- **AND** it SHALL record queue state showing the selected project id, policy, and active task id

#### Scenario: Queue waits for active Worker Run
- **WHEN** a run queue has an active Worker Run
- **THEN** the system SHALL NOT launch another queue task until the active Worker Run completes, fails, or is interrupted

#### Scenario: Queue continues after Review
- **WHEN** a queued Worker Run completes successfully and the task enters Review
- **AND** another eligible Estimated task remains in the same project
- **THEN** the queue SHALL be allowed to launch the next eligible task
- **AND** the prior Review task SHALL remain awaiting human disposition

### Requirement: Run queue respects launch guardrails and budget boundaries
Run automation SHALL use the existing board launch guardrails and SHALL NOT bypass budget, adapter, tracking-mode, or project-root requirements.

#### Scenario: Queue stops before budget override
- **WHEN** the next eligible task would require a launch budget override
- **THEN** the queue SHALL stop before launching that task
- **AND** the stop reason SHALL explain that operator budget approval is required

#### Scenario: Queue stops before native usage acknowledgement
- **WHEN** the next eligible task uses native usage tracking and requires explicit native budget acknowledgement
- **THEN** the queue SHALL stop before launching that task
- **AND** the system SHALL NOT auto-acknowledge native usage budget risk

#### Scenario: Queue rejects observed-only adapter
- **WHEN** the selected or default Worker Adapter is observed-only
- **THEN** run automation SHALL NOT launch the task
- **AND** the stop reason SHALL link the operator to Worker Setup or diagnostics

#### Scenario: Queue rejects mismatched project task
- **WHEN** a task is not bound to the selected project id
- **THEN** run automation SHALL NOT launch that task from the selected project queue

### Requirement: Run queue stop conditions are explicit
The system SHALL stop run automation when continuing would require manual, safety, setup, or budget decisions.

#### Scenario: Queue stops on retryable Worker failure
- **WHEN** a queued Worker Run fails retryably because the adapter exits nonzero, times out, or emits no required usage evidence
- **THEN** the failed task SHALL return to Estimated with inline launch evidence
- **AND** the queue SHALL stop with a retryable-failure stop reason

#### Scenario: Queue stops on hard safety block
- **WHEN** a queued Worker Run hits a hard safety or manual blocker
- **THEN** the affected task SHALL follow the existing Blocked lifecycle
- **AND** the queue SHALL stop with the hard blocker reason

#### Scenario: Queue stops when no eligible tasks remain
- **WHEN** all eligible Estimated tasks for the selected project have launched or are no longer eligible
- **THEN** the queue SHALL stop with a completed/no-eligible-tasks reason

#### Scenario: Operator stops queue
- **WHEN** the operator requests queue stop
- **THEN** the system SHALL stop launching additional tasks after the active Worker Run reaches its next terminal state
- **AND** it SHALL record operator stop as the reason

### Requirement: Auto Agent Review is optional and advisory
Run automation SHALL optionally trigger Agent Review after successful Worker Runs, but Auto Agent Review SHALL NOT perform Review Disposition.

#### Scenario: Auto Agent Review enabled
- **WHEN** a queued Worker Run completes successfully and enters Review
- **AND** Auto Agent Review is enabled for the automation policy
- **THEN** the system SHALL request Agent Review using the control-plane/orchestrator model
- **AND** it SHALL store the result on the Review task card as advisory evidence

#### Scenario: Auto Agent Review disabled
- **WHEN** a queued Worker Run completes successfully and enters Review
- **AND** Auto Agent Review is disabled
- **THEN** the task SHALL remain in Review without an automatic Agent Review request

#### Scenario: Auto Agent Review never marks done
- **WHEN** Auto Agent Review recommends approval
- **THEN** the task SHALL remain in Review until an operator manually marks it Done

### Requirement: Automation records evidence
Run automation SHALL record source, policy, actions, and stop reasons so operators can audit what the harness did.

#### Scenario: Auto-launched Worker Run records automation source
- **WHEN** a task is launched by `Run next task` or `Run queue`
- **THEN** the task or Worker Run metadata SHALL record the automation source and selected policy

#### Scenario: Queue stop reason is visible
- **WHEN** a run queue stops
- **THEN** the board SHALL show the latest queue stop reason for the selected project

#### Scenario: Automation events appear in timeline evidence
- **WHEN** run automation starts, launches a task, skips a task, stops, or requests Auto Agent Review
- **THEN** the system SHALL record a timeline or equivalent evidence event visible from board or session surfaces
