# project-archive-visibility Specification

## Purpose
TBD - created by archiving change archive-project-visibility. Update Purpose after archive.
## Requirements
### Requirement: Connected projects can be archived without deletion
The system SHALL let authenticated operators archive a connected project as a visibility-only action while preserving the connected-project row, filesystem repository, tasks, Worker Runs, sessions, token evidence, and review evidence.

#### Scenario: Archive active project
- **WHEN** an authenticated operator chooses Archive project for an active connected project
- **AND** the project has no Running tasks, active Worker Runs, or running queue automation
- **THEN** the system SHALL record project archive state with an archive timestamp
- **AND** the system SHALL NOT delete the connected-project row or any project task/session/evidence records
- **AND** the project SHALL be hidden from active project lists

#### Scenario: Archive blocked by running work
- **WHEN** an authenticated operator chooses Archive project for a connected project with Running tasks, active Worker Runs, or running queue automation
- **THEN** the system SHALL reject the archive action
- **AND** the response SHALL explain that running project work must finish or stop before archive
- **AND** the project SHALL remain active

### Requirement: Active project surfaces hide archived projects
The system SHALL exclude archived connected projects from normal active project surfaces while keeping archived projects discoverable through an explicit archived view or section.

#### Scenario: Active lists exclude archived projects
- **WHEN** an authenticated operator opens the Portal sidebar, `/projects`, setup project summary, or `/settings/project` active project section
- **THEN** archived connected projects SHALL NOT appear in those active project lists
- **AND** non-archived connected projects SHALL continue to appear normally

#### Scenario: Archived section lists archived projects
- **WHEN** one or more connected projects are archived
- **THEN** the Portal SHALL provide an explicit archived projects section or filter
- **AND** each archived project entry SHALL show its name, root path, archived state, and Restore action

#### Scenario: Empty active list ignores archived projects
- **WHEN** all connected projects are archived
- **THEN** active project surfaces SHALL behave as if there are no active projects
- **AND** they SHALL still provide the normal Open local repo action
- **AND** archived projects SHALL remain available through the archived section or filter

### Requirement: Archived project direct access preserves audit history
The system SHALL keep archived project URLs accessible for audit and restore while making archived state obvious and avoiding normal launch encouragement.

#### Scenario: Open archived project workspace directly
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an archived connected project
- **THEN** the workspace SHALL render the selected project with an archived banner
- **AND** the workspace SHALL provide a Restore project action
- **AND** task history and session evidence links SHALL remain available

#### Scenario: Archived project active board access is restore-first
- **WHEN** an authenticated operator opens `/projects/{project_id}/board` for an archived connected project
- **THEN** the response SHALL clearly indicate that the project is archived
- **AND** the response SHALL provide a Restore project action or route back to the archived workspace
- **AND** the system SHALL NOT launch new Worker work for the archived project unless it is restored first

### Requirement: Archived projects can be restored
The system SHALL let authenticated operators restore archived connected projects so they return to active project surfaces without losing existing project identity or history.

#### Scenario: Restore archived project
- **WHEN** an authenticated operator chooses Restore project for an archived connected project
- **THEN** the system SHALL remove project archive state
- **AND** the original connected project id and root path SHALL be preserved
- **AND** the project SHALL appear again in active project lists and project board routing

#### Scenario: Restore active project is harmless
- **WHEN** an authenticated operator chooses Restore project for a connected project that is already active
- **THEN** the project SHALL remain active
- **AND** no task, session, Worker Run, or evidence records SHALL be changed

### Requirement: Re-opening an archived repo does not duplicate project history
The local repo connection flow SHALL handle a root path that already belongs to an archived project without creating a duplicate connected project.

#### Scenario: Open local repo for archived project root
- **WHEN** an authenticated operator submits Open local repo for a root path that matches an archived connected project
- **THEN** the system SHALL NOT create a second connected project for the same root path
- **AND** the system SHALL restore the existing project or present a clear Restore project path
- **AND** existing project tasks, sessions, Worker Runs, and evidence SHALL remain bound to the original project id

