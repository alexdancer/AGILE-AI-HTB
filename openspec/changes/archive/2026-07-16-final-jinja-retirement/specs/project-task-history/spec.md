## MODIFIED Requirements

### Requirement: React project task history reaches presentation parity
When the complete React build is available, the canonical project task history page SHALL be presented by React: bookmarkable archive filters, full per-task evidence, and the inline restore path. React SHALL NOT change task lifecycle status, archive metadata semantics, or delete any task record. When the React build is missing or partial, the canonical URL SHALL return the missing-build recovery response; no server-rendered history page SHALL remain as fallback or oracle.

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

#### Scenario: Missing or partial build returns the recovery response at canonical task history
- **WHEN** an authenticated operator opens `/projects/{project_id}/task-history` while the React build is missing or partial
- **THEN** the system SHALL return the missing-build recovery response at the same canonical URL
- **AND** archive inspection and restore SHALL be unavailable until the frontend is built, rather than diverting to a server-rendered history page

#### Scenario: Unknown React project history is not found
- **WHEN** an authenticated operator opens the React project task history for a project id that does not exist
- **THEN** the system SHALL return a not-found response before serving any task data
