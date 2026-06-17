## MODIFIED Requirements

### Requirement: Launch errors surface inline on board

When `launch_task()` raises `TaskLaunchBlocked`, the route SHALL redirect to `/board` with the failure reasons in a query parameter. The board template SHALL render the error message as a dismissible banner and, when the failure is caused by adapter setup or verification, SHALL link the operator to `/settings/workers` for the simplified Worker Setup flow.

#### Scenario: Budget exceeded on launch

- **WHEN** task estimate exceeds remaining worker_execution budget
- **AND** operator clicks "Launch task" without budget override
- **THEN** the board shows "Task estimate exceeds remaining launch budget" in an error banner

#### Scenario: Adapter not launch-ready on launch

- **WHEN** operator clicks "Launch task" with an adapter that is unconfigured or unverified
- **THEN** the board shows the launch guardrail failure reasons in an error banner
- **AND** the banner includes a link to `/settings/workers` to complete Worker Setup

#### Scenario: Successful launch removes error

- **WHEN** a previous error was shown
- **AND** operator loads the board normally with no error query param
- **THEN** no error banner is displayed
