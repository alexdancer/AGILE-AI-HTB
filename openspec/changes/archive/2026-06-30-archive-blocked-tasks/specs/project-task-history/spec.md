## MODIFIED Requirements

### Requirement: Archived task history preserves evidence and restore path
Archived tasks SHALL remain normal task records with their lifecycle status, Worker Run/session links, token evidence, blocked evidence, and review evidence intact.

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
