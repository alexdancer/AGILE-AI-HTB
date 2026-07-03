## MODIFIED Requirements

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
