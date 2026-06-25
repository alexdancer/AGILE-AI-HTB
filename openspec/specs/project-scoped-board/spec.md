# project-scoped-board Specification

## Purpose
Define project-scoped board behavior so operators work on tasks for one connected project at a time while preserving safe compatibility redirects from the legacy global board entry point.

## Requirements

### Requirement: Project board route displays selected project tasks
The system SHALL provide a project-scoped task board for each connected project and SHALL only display task cards bound to that selected project.

#### Scenario: Project board shows only selected project tasks
- **WHEN** an authenticated operator opens `/projects/{project_id}/board` for an existing connected project
- **AND** tasks exist for multiple connected projects
- **THEN** the board SHALL show only tasks whose project binding matches `{project_id}`
- **AND** the board SHALL pass the selected project as `active_project` for sidebar/header context

#### Scenario: Unknown project board is not found
- **WHEN** an authenticated operator opens `/projects/{project_id}/board` for an unknown connected project id
- **THEN** the system SHALL return a not found response

### Requirement: Project board task intake binds tasks to selected project
The system SHALL bind every task created from a project board intake flow to the selected connected project before the task appears on the board.

#### Scenario: Estimate form creates project-bound task
- **WHEN** an authenticated operator submits the estimate form from `/projects/{project_id}/board`
- **THEN** the created task SHALL include metadata for `connected_project_id`, `project_root_path`, and `project_profile` from the selected project
- **AND** the response SHALL redirect back to `/projects/{project_id}/board`

#### Scenario: Direct task creation with project context creates project-bound task
- **WHEN** the system creates a task from a project-aware route or server-side project context
- **THEN** the task SHALL include the selected connected project binding metadata

### Requirement: Project task breakdown preserves project binding
The system SHALL preserve selected project binding through markdown/paste task breakdown review and acceptance.

#### Scenario: Breakdown review created from project board keeps project context
- **WHEN** an operator submits markdown or long task intake from `/projects/{project_id}/board`
- **THEN** the task breakdown review SHALL retain selected project metadata in its intake metadata
- **AND** review actions SHALL redirect back to project-aware pages when possible

#### Scenario: Accepted breakdown candidates become project tasks
- **WHEN** an operator accepts one or more candidates from a project-bound task breakdown
- **THEN** every created task SHALL include `connected_project_id`, `project_root_path`, and `project_profile` from the source project
- **AND** the operator SHALL return to `/projects/{project_id}/board`

### Requirement: Global board route is safe compatibility entry
The system SHALL avoid presenting `/board` as an ambiguous launch surface when project workspaces exist.

#### Scenario: Global board redirects to recent project board
- **WHEN** an authenticated operator opens `/board`
- **AND** at least one connected project exists
- **THEN** the system SHALL redirect to `/projects/{project_id}/board` for the most recently updated connected project

#### Scenario: Global board redirects to projects without connected projects
- **WHEN** an authenticated operator opens `/board`
- **AND** no connected projects exist
- **THEN** the system SHALL redirect to `/projects`

### Requirement: Run automation remains bound to selected project board
Project board run automation SHALL launch only tasks that are bound to the selected connected project.

#### Scenario: Queue only sees selected project tasks
- **WHEN** an operator starts run automation from `/projects/{project_id}/board`
- **THEN** the automation SHALL consider only tasks whose metadata is bound to `{project_id}`

#### Scenario: Queue does not fall back to another project
- **WHEN** no eligible tasks exist for the selected project
- **AND** another connected project has eligible tasks
- **THEN** the selected project's run automation SHALL NOT launch tasks from the other project
- **AND** it SHALL report that no eligible tasks exist for the selected project

#### Scenario: Project mismatch blocks automation launch
- **WHEN** run automation attempts to launch a task whose bound project id differs from the selected project id
- **THEN** the launch SHALL be rejected before starting any Worker Adapter process

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
