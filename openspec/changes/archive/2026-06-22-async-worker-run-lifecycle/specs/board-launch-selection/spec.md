## MODIFIED Requirements

### Requirement: Board launch form includes adapter selector
The board task card for Estimated tasks SHALL include a dropdown selector listing all worker adapters. The initially selected adapter SHALL be the default adapter if one is set, otherwise the first adapter in the list. The board SHALL NOT require or render a Ready column for launchable tasks.

#### Scenario: Multiple adapters available
- **WHEN** two or more adapters exist in the database
- **AND** a task is in the Estimated column
- **THEN** the launch form shows a `<select>` with all adapter names
- **AND** the default adapter is pre-selected

#### Scenario: No default adapter set
- **WHEN** no adapter has `is_default` set
- **AND** a task is in the Estimated column
- **THEN** the first adapter in the list is pre-selected

### Requirement: Launch button always visible for launchable tasks
The "Launch task" button SHALL render for all tasks in the Estimated column regardless of adapter verification state. The `has_verified_worker_adapter` gate SHALL be removed from the board template. Ready SHALL NOT be a canonical launch column.

#### Scenario: No verified adapter exists
- **WHEN** no adapter is verified
- **AND** a task is in the Estimated column
- **THEN** the "Launch task" button is visible

#### Scenario: Launch fails due to unverified adapter
- **WHEN** operator clicks "Launch task" with no verified adapter
- **THEN** the request returns a redirect or JSON response with launch guardrail failure reasons
- **AND** the board displays an error banner with the launch guardrail failure reasons

### Requirement: Launch errors surface inline on board
When a Worker Run fails retryably, the board template SHALL render the failure on the affected task card while preserving the task's Estimated column and launch form. When `launch_task()` rejects a pre-launch guardrail, the route SHALL return the failure reasons in the response or redirect. When the failure is caused by adapter setup or verification, the UI SHALL link the operator to `/settings/workers` for the simplified Worker Setup flow.

#### Scenario: Budget exceeded on launch
- **WHEN** task estimate exceeds remaining worker_execution budget
- **AND** operator clicks "Launch task" without budget override
- **THEN** the board shows "Task estimate exceeds remaining launch budget" in an error banner

#### Scenario: Native usage budget override requires acknowledgement
- **WHEN** task estimate exceeds remaining worker_execution budget
- **AND** the selected Worker Adapter uses `native_usage` tracking mode
- **AND** operator chooses to launch with budget override
- **THEN** the board requires acknowledgement that native usage cannot be request-throttled mid-run
- **AND** the launched Worker Run records `budget_override=true`
- **AND** post-run reconciliation may report a budget overrun after native usage evidence is imported

#### Scenario: Adapter not launch-ready on launch
- **WHEN** operator clicks "Launch task" with an adapter that is unconfigured or unverified
- **THEN** the board shows the launch guardrail failure reasons in an error banner
- **AND** the banner includes a link to `/settings/workers` to complete Worker Setup

#### Scenario: Successful launch removes error
- **WHEN** a previous error was shown
- **AND** operator launches the task successfully
- **THEN** the previous retryable launch error no longer appears as the current error

#### Scenario: Recoverable worker failure stays relaunchable
- **WHEN** a Running task's Worker Run fails because the Worker command exits nonzero, times out, or emits no required usage evidence
- **THEN** the task returns to the Estimated column
- **AND** the task card shows the recoverable launch failure message and sanitized evidence
- **AND** the task card still shows the launch form for retry

### Requirement: Blocked column is reserved for workflow blockers
The board SHALL use the Blocked column for workflow or dependency blockers, manual-estimate-required tasks, and hard safety guardrail states, not for retryable Worker Run failures on otherwise launchable tasks.

#### Scenario: Operator sees dependency block separately from launch failure
- **WHEN** one task has workflow dependency metadata and another task has a recent Worker timeout
- **THEN** only the dependency-blocked task appears in the Blocked column
- **AND** the timed-out task appears in Estimated with inline launch-error copy

## ADDED Requirements

### Requirement: Board remains navigable during Worker Run
The board SHALL return control to the operator immediately after a Worker Run starts and SHALL remain navigable while the Worker Run continues in the background.

#### Scenario: Launch does not block page navigation
- **WHEN** an operator clicks Launch for an Estimated task
- **AND** the Worker Adapter command is still running
- **THEN** the board shows the task in Running or otherwise returns a non-blocking launch response
- **AND** the operator can navigate to other portal pages without waiting for Worker completion

### Requirement: Running and Review reflect Worker Run state
The board SHALL use Running for active Worker Runs and Review for completed Worker Runs awaiting operator inspection.

#### Scenario: Active run appears Running
- **WHEN** a Worker Run is active for a task
- **THEN** the task appears in the Running column with active run metadata

#### Scenario: Completed run appears Review
- **WHEN** a Worker Run completes successfully with required evidence
- **THEN** the task appears in the Review column with a link or inline summary for run evidence

## REMOVED Requirements

### Requirement: Ready launch column
**Reason**: Estimated already represents the launchable pre-run state once estimate/model/adapter guardrails pass, and Ready creates redundant board semantics.
**Migration**: Treat existing Ready tasks as Estimated and stop creating or rendering the Ready column.
