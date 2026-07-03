# board-launch-selection

## Purpose

Enable operators to select which worker adapter and model to use when launching tasks from the board, with the launch button always visible for Estimated tasks, no redundant Ready launch column, asynchronous Worker Run state visible on the board, and failure reasons surfaced inline.
## Requirements
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

### Requirement: Model selector filters by selected adapter
The board launch form SHALL include a model selector populated from the selected adapter's allowed Worker models. Changing the adapter selection SHALL update the model dropdown to show only that adapter's allowed models.

#### Scenario: Adapter has allowed models
- **WHEN** operator selects an adapter with allowed models `["opencode/gpt-5.1", "opencode/gpt-5.2"]`
- **THEN** the model dropdown shows those two models

#### Scenario: Adapter has discovered models but no allowed models
- **WHEN** operator selects an adapter with discovered models but an empty allowed model set
- **THEN** the model dropdown does not offer an unapproved fallback model
- **AND** launch guardrails keep the task from launching until at least one model is allowed

#### Scenario: Switching adapter updates model list
- **WHEN** operator changes adapter selection from OpenCode to Claude Code
- **THEN** the model dropdown updates to show Claude Code's allowed models

### Requirement: Launch button always visible for launchable tasks
The "Launch task" button SHALL render for all tasks in the Estimated column regardless of adapter verification state. The `has_verified_worker_adapter` gate SHALL be removed from the board template. Ready SHALL NOT be a canonical launch column.

#### Scenario: No verified adapter exists
- **WHEN** no adapter is verified
- **AND** a task is in the Estimated column
- **THEN** the "Launch task" button is visible

#### Scenario: Launch fails due to unverified adapter
- **WHEN** operator clicks "Launch task" with no verified adapter
- **THEN** the request returns a redirect to `/board?error=...`
- **AND** the board displays an error banner with the launch guardrail failure reasons

### Requirement: Launch errors surface inline on board
When a Worker Run fails retryably, the board template SHALL render the failure on the affected task card while preserving the task's Estimated column and launch form. When `launch_task()` rejects a pre-launch guardrail, the route SHALL return the failure reasons in the response or redirect. When the failure is caused by adapter setup or verification, the UI SHALL link the operator to `/settings/workers` for the simplified Worker Setup flow. When a native usage budget override is required, the UI SHALL require acknowledgement that native usage cannot be request-throttled mid-run.

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
- **WHEN** operator clicks "Launch task" with an adapter that is unconfigured, unverified, or observed-only
- **THEN** the board shows the launch guardrail failure reasons in an error banner
- **AND** the banner includes a link to `/settings/workers` to complete Worker Setup

#### Scenario: Successful launch removes error
- **WHEN** a previous error was shown
- **AND** operator loads the board normally (no error query param)
- **THEN** no error banner is displayed

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

### Requirement: Board remains navigable during Worker Run
The board SHALL return control to the operator immediately after a Worker Run starts and SHALL remain navigable while the Worker Run continues in the background.

#### Scenario: Launch does not block page navigation
- **WHEN** an operator clicks Launch for an Estimated task
- **AND** the Worker Adapter command is still running
- **THEN** the board shows the task in Running or otherwise returns a non-blocking launch response
- **AND** the operator can navigate to other portal pages without waiting for Worker completion

### Requirement: Running and Review reflect Worker Run state
The board SHALL use Running for active Worker Runs and Review for completed Worker Runs awaiting operator inspection. Review task cards SHALL show completed run evidence, expose review actions, and display the latest operator review prompt and Agent Review response when present.

#### Scenario: Active run appears Running
- **WHEN** a Worker Run is active for a task
- **THEN** the task appears in the Running column with active run metadata

#### Scenario: Completed run appears Review
- **WHEN** a Worker Run completes successfully with required evidence
- **THEN** the task appears in the Review column with a link or inline summary for run evidence
- **AND** the card shows Review actions for Agent Review, Mark Done, and Block
- **AND** the card provides an input for an optional operator review prompt or focus

#### Scenario: Review card displays saved prompt
- **WHEN** a Review task has a saved operator review prompt
- **THEN** the Review task card displays that prompt on the task card

#### Scenario: Review card displays Agent Review response
- **WHEN** a Review task has a completed Agent Review result
- **THEN** the Review task card displays the latest Agent Review summary or response
- **AND** the response includes a visible completion indicator without requiring the operator to expand raw details

#### Scenario: Agent Review action returns to visible result
- **WHEN** an operator submits Agent Review from a Review task card
- **AND** the Agent Review action completes or fails
- **THEN** the board response after redirect or refresh shows a visible Agent Review status line on that task card
- **AND** the line includes the review recommendation or failure state, review session id when available, and token total when available

### Requirement: Board shows tracking mode strength
The board SHALL show tracking-mode-specific launch copy for the selected Worker Adapter without collapsing all launchable adapters into a generic governed state.

#### Scenario: Native usage adapter selected
- **WHEN** an Estimated task's selected Worker Adapter uses `native_usage` tracking mode
- **THEN** the board shows `Tracking: Tracked via Native Usage`
- **AND** the board shows `Runtime request guardrails: Not available`
- **AND** the board shows `Accounting: Budget-authoritative after run`

#### Scenario: Proxy-governed adapter selected
- **WHEN** an Estimated task's selected Worker Adapter uses `proxy_governed` tracking mode
- **THEN** the board shows `Tracking: Governed via Harness Proxy`
- **AND** the board shows `Runtime request guardrails: Available`
- **AND** the board shows `Accounting: Budget-authoritative during run`

#### Scenario: Observed-only adapter selected
- **WHEN** an Estimated task's selected Worker Adapter uses `observed_only` tracking mode
- **THEN** the board keeps Launch guardrail-blocked
- **AND** the board links the operator to Worker Setup diagnostics instead of launching the Task

### Requirement: Board launch requires task-bound project root
The system SHALL require a connected project root before launching a normal Worker task from the board, and project-scoped board launches SHALL require the task's project binding to match the selected project board context.

#### Scenario: Launch uses selected project task root
- **WHEN** an authenticated operator launches an Estimated task from `/projects/{project_id}/board`
- **AND** the task metadata is bound to `{project_id}`
- **AND** the bound project root matches a connected project record
- **THEN** the system SHALL pass that task-bound project root path as the Worker launch workdir
- **AND** the Worker Run evidence SHALL record the selected project id and project root used for the launch

#### Scenario: Launch fails without connected project
- **WHEN** an authenticated operator launches an Estimated task from a board entry point
- **AND** no connected project exists
- **THEN** the system SHALL reject the launch before starting any Worker Adapter process
- **AND** `/board` SHALL redirect the operator to `/projects` to connect a project

#### Scenario: Launch rejects task not bound to selected project
- **WHEN** an authenticated operator launches an Estimated task from `/projects/{project_id}/board`
- **AND** the task metadata is missing a project binding or is bound to a different connected project id
- **THEN** the system SHALL reject the launch before starting any Worker Adapter process
- **AND** the task SHALL remain eligible for correction or recreation rather than launching against another repository

### Requirement: Board launch binds OpenCode project directory explicitly
The system SHALL bind OpenCode Worker launches to the task-bound connected project root using OpenCode's explicit project-directory option rather than relying only on subprocess cwd.

#### Scenario: OpenCode launch command includes project directory
- **WHEN** the selected Worker Adapter is OpenCode
- **AND** the task-bound connected project root is `/repo/example`
- **THEN** the launch command plan SHALL include `opencode run --dir /repo/example`
- **AND** the command plan SHALL NOT rely on cwd alone as evidence of the project boundary

### Requirement: Board task cards default to compact readable content
The board SHALL render task cards with a compact default view that keeps the task summary, key estimate/model metadata, and the current primary action visible while placing verbose evidence and diagnostics behind native expandable details.

#### Scenario: Long task description is compact by default
- **WHEN** a task has a long description
- **AND** the operator opens the board
- **THEN** the task card shows a shortened visual summary in the default card view
- **AND** the full task description remains available from the same card without navigating away

#### Scenario: Verbose run evidence is collapsed by default
- **WHEN** a task has Worker timeline events, launch stdout, stderr, Agent Review findings, or diagnostic evidence
- **AND** the operator opens the board
- **THEN** the verbose evidence is available behind native expandable details
- **AND** the card still shows the relevant primary action for its status without opening the details

#### Scenario: Existing board workflow remains unchanged
- **WHEN** the board renders Estimated, Running, Review, Done, and Blocked tasks
- **THEN** the existing board columns remain available
- **AND** the existing launch, refresh, review, done, and block actions remain available for their current statuses

### Requirement: Board displays actual launched model before recommendation
When a task has launch evidence for a Worker model, the board SHALL display that launched model as the primary model value. If the launched model differs from the recommended estimate model, the board SHALL preserve and display the recommended model as secondary evidence.

#### Scenario: Operator launches with recommended model
- **WHEN** a task is launched with the same model as `recommended_model`
- **THEN** the board shows that model as the primary model value
- **AND** the board does not duplicate the same model as a separate recommendation warning

#### Scenario: Operator overrides recommended model at launch
- **WHEN** a task has `recommended_model` set to `gpt-5.4-mini`
- **AND** the operator launches the task with `openai/gpt-5.5 --variant high`
- **THEN** the board shows `openai/gpt-5.5 --variant high` as the primary launched model value
- **AND** the board still shows `gpt-5.4-mini` as the recommended estimate model in secondary evidence

#### Scenario: Task has not launched yet
- **WHEN** a task has no launch model evidence
- **AND** it has a `recommended_model`
- **THEN** the board shows the recommended model as the primary model value

### Requirement: Board live-refreshes active Worker Runs
The board SHALL keep active Worker Run status current without requiring the operator to click Refresh status manually.

#### Scenario: Running task completes while board is open
- **WHEN** an operator has the board open with a Running task
- **AND** the task's Worker Run completes successfully
- **THEN** the board SHALL update so the task appears in Review without requiring a manual Refresh status click

#### Scenario: Running task fails retryably while board is open
- **WHEN** an operator has the board open with a Running task
- **AND** the task's Worker Run fails retryably
- **THEN** the board SHALL update so the task appears in Estimated with inline launch failure evidence

#### Scenario: Manual refresh remains available
- **WHEN** live refresh is unavailable or disabled
- **THEN** the existing manual Refresh status action SHALL remain available for Running tasks

### Requirement: Board automation controls preserve manual launch
The board SHALL add automation controls without removing existing per-task Launch controls for Estimated tasks.

#### Scenario: Operator can still launch a single card manually
- **WHEN** an Estimated task appears on the board
- **THEN** the task card SHALL still expose the existing adapter/model launch form
- **AND** automation controls SHALL NOT be required to launch the task

### Requirement: Launch controls preserve model-layer clarity
Board launch controls SHALL keep Worker Adapter selection, Worker model selection, and estimator recommendation provenance visually distinct.

#### Scenario: Launch model differs from recommendation
- **WHEN** a task has a recommended model and a different selected or launched Worker model
- **THEN** the board SHALL display the selected/launched Worker model as the primary run model
- **AND** it SHALL keep the estimator recommendation visible as secondary provenance rather than overwriting it

#### Scenario: Adapter and tracking label remain visible
- **WHEN** an Estimated task offers launch controls
- **THEN** the control SHALL show the Worker Adapter identity separately from the tracking label or usage-authority mode

