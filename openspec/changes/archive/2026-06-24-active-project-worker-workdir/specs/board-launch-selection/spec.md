## ADDED Requirements

### Requirement: Board launch requires active project root
The system SHALL require a connected project root before launching a normal Worker task from the board.

#### Scenario: Launch uses connected project root
- **WHEN** an authenticated operator launches an Estimated task from the board
- **AND** at least one connected project exists
- **THEN** the system SHALL pass the active connected project's root path as the Worker launch workdir
- **AND** the Worker Run evidence SHALL record the selected project root used for the launch

#### Scenario: Launch fails without connected project
- **WHEN** an authenticated operator launches an Estimated task from the board
- **AND** no connected project exists
- **THEN** the system SHALL reject the launch before starting any Worker Adapter process
- **AND** the board SHALL show a setup error linking the operator to `/projects`

### Requirement: Board launch binds OpenCode project directory explicitly
The system SHALL bind OpenCode Worker launches to the active project root using OpenCode's explicit project-directory option rather than relying only on subprocess cwd.

#### Scenario: OpenCode launch command includes project directory
- **WHEN** the selected Worker Adapter is OpenCode
- **AND** the active project root is `/repo/example`
- **THEN** the launch command plan SHALL include `opencode run --dir /repo/example`
- **AND** the command plan SHALL NOT rely on cwd alone as evidence of the project boundary
