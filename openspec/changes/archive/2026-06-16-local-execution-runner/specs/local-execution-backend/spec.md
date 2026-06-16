## ADDED Requirements

### Requirement: All-in-one local runner mode
The system SHALL provide an all-in-one local mode that runs the Control Plane and a Local Runner Execution Backend on the same machine.

#### Scenario: Start local runner mode
- **WHEN** the operator starts the harness with local runner mode enabled
- **THEN** the Portal, Harness Proxy, token ledger, and Local Runner Execution Backend are available from the same local harness instance

### Requirement: Connect local project path
The system SHALL allow the User to connect a local repository path as a Connected Project for local execution.

#### Scenario: Valid local repo path
- **WHEN** the User submits a readable local directory path that looks like a project
- **THEN** the system stores it as a Connected Project and creates a lightweight Project Profile

#### Scenario: Invalid local repo path
- **WHEN** the User submits a missing, unreadable, or non-directory path
- **THEN** the system rejects the connection and shows a clear validation failure

### Requirement: Lightweight Project Profile
The system SHALL derive lightweight project context for connected projects without scanning arbitrary source files during normal task breakdown.

#### Scenario: Project profile detection
- **WHEN** a local project is connected
- **THEN** the system records project name, root path, git branch when available, language/framework hints, package manager hints, test command when detectable, run command when detectable, top-level folders, and relevant docs such as README, CONTEXT.md, and HARNESS.md

### Requirement: Project capability states
The system SHALL expose project capability states that distinguish analysis readiness from launch readiness.

#### Scenario: Local runner project is launch-ready
- **WHEN** a connected local project has a valid path, online Local Runner backend, and verified launchable Worker Adapter
- **THEN** the Portal shows the project as Launch-ready via Local Runner

#### Scenario: Analysis-only project is not launchable
- **WHEN** a project has enough context for breakdown and estimation but no verified execution backend
- **THEN** the Portal shows the project as Analysis-ready and disables Worker launch

#### Scenario: Blocked project lacks execution backend
- **WHEN** a project cannot satisfy Launch Guardrails
- **THEN** the Portal shows the project or task as Blocked with the missing capability reason
