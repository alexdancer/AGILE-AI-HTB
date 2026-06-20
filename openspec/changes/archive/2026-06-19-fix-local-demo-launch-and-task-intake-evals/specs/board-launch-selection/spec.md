## MODIFIED Requirements

### Requirement: Launch errors surface inline on board
When `launch_task()` raises `TaskLaunchBlocked`, the route SHALL redirect to `/board` with the failure reasons in a query parameter. The board template SHALL render the error message as a dismissible banner and, when the failure is caused by adapter setup or verification, SHALL link the operator to `/settings/workers` for the simplified Worker Setup flow. Recoverable Worker runtime failures for launchable tasks SHALL also render on the affected task card while preserving the task's launchable column and launch form.

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
- **AND** operator loads the board normally (no error query param)
- **THEN** no error banner is displayed

#### Scenario: Recoverable worker failure stays relaunchable
- **WHEN** an Estimated or Ready task launch fails because the Worker command exits nonzero, times out, or emits no required usage evidence
- **THEN** the task remains in its pre-launch Estimated or Ready column
- **AND** the task card shows the recoverable launch failure message and sanitized evidence
- **AND** the task card still shows the launch form for retry

## ADDED Requirements

### Requirement: Blocked column is reserved for workflow blockers
The board SHALL use the Blocked column for workflow or dependency blockers, manual-estimate-required tasks, and hard safety guardrail states, not for recoverable Worker runtime failures on otherwise launchable tasks.

#### Scenario: Operator sees dependency block separately from launch failure
- **WHEN** one task has workflow dependency metadata and another Estimated task has a recent Worker timeout
- **THEN** only the dependency-blocked task appears in the Blocked column
- **AND** the timed-out task remains launchable with inline launch-error copy
