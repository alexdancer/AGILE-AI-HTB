## ADDED Requirements

### Requirement: Project board shows compact operating status
The project-scoped board SHALL show compact operating status for the selected project before task columns.

#### Scenario: Board toolbar summarizes project work
- **WHEN** an authenticated operator opens `/projects/{project_id}/board`
- **THEN** the board SHALL show the selected project identity, column counts, Worker launch readiness, and any active run/queue/refresh status available to the route
- **AND** the status summary SHALL NOT replace existing manual task intake, launch, refresh, or review controls

### Requirement: Board columns have useful empty states
Each project board column SHALL explain what belongs there when empty.

#### Scenario: Empty columns explain next step
- **WHEN** a project board column has no tasks
- **THEN** the column SHALL show concise empty-state copy specific to that column's lifecycle purpose
- **AND** the Estimated column empty state SHALL point operators toward task intake when appropriate

### Requirement: Board failure states are visibly distinct
The project board SHALL visually and textually distinguish launch errors, launch guardrail blocks, manual Blocked review decisions, and manual-estimate requirements.

#### Scenario: Retryable launch failure remains relaunchable
- **WHEN** a retryable Worker launch failure is displayed on an Estimated task
- **THEN** the card SHALL label it as launch failure evidence
- **AND** it SHALL keep relaunch/setup actions visible when allowed by existing guardrails

#### Scenario: Human blocked task explains disposition
- **WHEN** a task is in Blocked because an operator blocked it during Review
- **THEN** the card SHALL show the human-provided blocked reason separately from adapter launch errors or setup blockers
