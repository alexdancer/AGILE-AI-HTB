# project-task-history Specification

## Purpose
TBD - created by archiving change add-project-task-history-archive. Update Purpose after archive.
## Requirements
### Requirement: Project task history page lists repo tasks
The system SHALL provide a project-scoped task history page that lists task cards for one connected repository outside the active board.

#### Scenario: Project history shows repo tasks
- **WHEN** an authenticated operator opens `/projects/{project_id}/task-history` for an existing connected project
- **AND** tasks exist for that project in any lifecycle status
- **THEN** the page SHALL show tasks whose project binding matches `{project_id}`
- **AND** the page SHALL include both archived and unarchived tasks by default or through visible filters
- **AND** the page SHALL NOT show tasks bound to other projects

#### Scenario: Unknown project history is not found
- **WHEN** an authenticated operator opens `/projects/{project_id}/task-history` for an unknown connected project id
- **THEN** the system SHALL return a not found response

### Requirement: Project task history supports archive-oriented filters
The project task history page SHALL let operators distinguish active board tasks from archived tasks without losing access to either set.

#### Scenario: Archived filter shows archived cards
- **WHEN** an authenticated operator opens the project task history page with the archived filter selected
- **THEN** the page SHALL show tasks whose metadata contains archive state for the selected project
- **AND** each archived task SHALL show that it is archived

#### Scenario: Active filter excludes archived cards
- **WHEN** an authenticated operator opens the project task history page with the active filter selected
- **THEN** the page SHALL show selected-project tasks that do not have archive state
- **AND** archived tasks SHALL be excluded from that filtered view

### Requirement: Archived task history preserves evidence and restore path
Archived tasks SHALL remain normal task records with their lifecycle status, Worker Run/session links, token evidence, blocked evidence, review evidence, estimate evidence, and restore path intact.

#### Scenario: Archived Done task keeps evidence
- **WHEN** a Done task is archived
- **THEN** the project task history page SHALL still show the task description, lifecycle status, estimate/actual token evidence when present, and links to session or Worker evidence when present
- **AND** the task SHALL remain `Done`
- **AND** the task row SHALL NOT be deleted

#### Scenario: Archived Blocked task keeps evidence
- **WHEN** a Blocked task is archived
- **THEN** the project task history page SHALL still show the task description, lifecycle status, estimate/actual token evidence when present, blocked reason or manual-estimate evidence when present, and links to session or Worker evidence when present
- **AND** the task SHALL remain `Blocked`
- **AND** the task row SHALL NOT be deleted

#### Scenario: Dismissed Estimated task keeps estimate evidence
- **WHEN** an Estimated task is dismissed from the selected project board
- **THEN** the project task history page SHALL still show the task description, lifecycle status, estimate token evidence when present, recommended model when present, and archive state
- **AND** the task SHALL remain `Estimated`
- **AND** the task row SHALL NOT be deleted

#### Scenario: Operator unarchives archived Done task
- **WHEN** an authenticated operator chooses Unarchive for an archived Done task from project task history
- **THEN** the system SHALL remove the task archive state
- **AND** the task SHALL remain `Done`
- **AND** the task SHALL be eligible to appear in the selected project's Done board column again

#### Scenario: Operator unarchives archived Blocked task
- **WHEN** an authenticated operator chooses Unarchive for an archived Blocked task from project task history
- **THEN** the system SHALL remove the task archive state
- **AND** the task SHALL remain `Blocked`
- **AND** the task SHALL be eligible to appear in the selected project's Blocked board column again

#### Scenario: Operator unarchives dismissed Estimated task
- **WHEN** an authenticated operator chooses Unarchive for an archived Estimated task from project task history
- **THEN** the system SHALL remove the task archive state
- **AND** the task SHALL remain `Estimated`
- **AND** the task SHALL be eligible to appear in the selected project's Estimated board column again

### Requirement: React project task history reaches presentation parity
When the complete React build is available, the canonical project task history page SHALL be presented by React with parity to the existing Jinja page: bookmarkable archive filters, full per-task evidence, and the inline restore path. React SHALL NOT change task lifecycle status, archive metadata semantics, or delete any task record, and the Jinja history page SHALL remain the missing/partial-build fallback and parity oracle.

#### Scenario: React history shows the same filtered repo tasks
- **WHEN** an authenticated operator opens the React project task history for an existing project with a selected archive filter
- **THEN** React SHALL show the selected-project tasks matching that filter using authenticated FastAPI data
- **AND** React SHALL NOT show tasks bound to other projects
- **AND** the archive filter selection SHALL remain bookmarkable through the canonical query

#### Scenario: React history preserves archived task evidence and restore path
- **WHEN** an authenticated operator views an archived task in the React project task history
- **THEN** React SHALL show the task description, lifecycle status, estimate/actual token evidence when present, recommended model when present, blocked reason or manual-estimate evidence when present, archive state and timestamp, and session or Worker evidence links when present
- **AND** React SHALL present an inline Unarchive action for archived tasks
- **AND** the task record SHALL NOT be deleted

#### Scenario: React unarchive restores the task without status change
- **WHEN** an authenticated operator uses the inline Unarchive action in the React project task history for an archived task
- **THEN** the system SHALL remove the task archive state using the existing authoritative unarchive behavior
- **AND** the task lifecycle status SHALL be unchanged
- **AND** React SHALL refresh authoritative history state so the restored task reflects its removed archive state

#### Scenario: Unknown React project history is not found
- **WHEN** an authenticated operator opens the React project task history for a project id that does not exist
- **THEN** the system SHALL return a not-found response before serving any task data

