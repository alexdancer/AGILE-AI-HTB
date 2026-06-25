## ADDED Requirements

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
