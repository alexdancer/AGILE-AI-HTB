# execution-floor Specification

## Purpose
TBD - created by archiving change two-surface-orchestration-board. Update Purpose after archive.
## Requirements
### Requirement: Execution Floor renders live and completed work
The system SHALL provide an Execution Floor surface at the canonical `/projects/{project_id}/floor` URL that shows active Worker Runs, tasks awaiting review, and recently completed work for the selected project, using the existing authoritative board payload. FastAPI SHALL remain authoritative for all run, review, and lifecycle state.

#### Scenario: Floor shows active runs, review queue, and finished trail
- **WHEN** an authenticated operator opens `/projects/{project_id}/floor` while the complete React build is available
- **THEN** the Floor SHALL render one pane per active Worker Run, a review queue of tasks in Review, and a recently-finished trail
- **AND** it SHALL show only work bound to `{project_id}`

#### Scenario: Missing or partial build returns the recovery response
- **WHEN** an authenticated operator opens `/projects/{project_id}/floor` while the React build is missing or partial
- **THEN** the system SHALL return the missing-build recovery response at the same canonical URL

#### Scenario: Unknown project is not found
- **WHEN** an authenticated operator opens `/projects/{project_id}/floor` for an unknown connected project id
- **THEN** the backend SHALL return a not found response

### Requirement: Execution Floor represents concurrent active runs while queue launch remains serial
The Execution Floor SHALL render every active Worker Run pane for the project while queue automation launches at most one queue-owned run at a time. Board automation state SHALL represent active runs as a collection rather than a single active run and SHALL remain compatible with legacy singular persisted state.

#### Scenario: One active run renders as a single pane
- **WHEN** exactly one Worker Run is active for the project
- **THEN** the Floor SHALL render one run pane
- **AND** the run-queue behavior SHALL remain one-at-a-time

#### Scenario: Board automation state is a collection
- **WHEN** the system records active project runs
- **THEN** it SHALL store and project active runs as a list
- **AND** independently active runs SHALL remain monitorable while the queue policy remains one-at-a-time

### Requirement: Recently-finished trail leads with estimate versus actual
The Execution Floor recently-finished trail SHALL show each completed task's estimated tokens and actual tokens together as the leading fact, and SHALL offer Archive to move a task to Task History.

#### Scenario: Finished task shows estimate and actual
- **WHEN** a task has completed with recorded actual tokens
- **THEN** the finished trail entry SHALL display estimated tokens and actual tokens as its primary content
- **AND** it SHALL provide an Archive action that moves the task to Task History

