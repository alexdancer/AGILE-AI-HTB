# board-launch-selection

## Purpose

Enable operators to select which worker adapter and model to use when launching tasks from the board, with the launch button always visible for Estimated and Ready tasks and failure reasons surfaced as inline error banners.

## Requirements

### Requirement: Board launch form includes adapter selector
The board task card for Estimated and Ready tasks SHALL include a dropdown selector listing all worker adapters. The initially selected adapter SHALL be the default adapter if one is set, otherwise the first adapter in the list.

#### Scenario: Multiple adapters available
- **WHEN** two or more adapters exist in the database
- **THEN** the launch form shows a `<select>` with all adapter names
- **AND** the default adapter is pre-selected

#### Scenario: No default adapter set
- **WHEN** no adapter has `is_default` set
- **THEN** the first adapter in the list is pre-selected

### Requirement: Model selector filters by selected adapter
The board launch form SHALL include a model selector populated from the selected adapter's `supported_models`. Changing the adapter selection SHALL update the model dropdown to show only that adapter's models.

#### Scenario: Adapter has discovered models
- **WHEN** operator selects an adapter with `supported_models: ["opencode/gpt-5.1", "gpt-5.1-codex"]`
- **THEN** the model dropdown shows those two models

#### Scenario: Adapter has no discovered models
- **WHEN** operator selects an adapter with empty `supported_models`
- **THEN** the model dropdown shows a single option: the task's `recommended_model` with a "(no discovered models)" note

#### Scenario: Switching adapter updates model list
- **WHEN** operator changes adapter selection from OpenCode to Claude Code
- **THEN** the model dropdown updates to show Claude Code's supported models

### Requirement: Launch button always visible for launchable tasks
The "Launch task" button SHALL render for all tasks in Estimated or Ready columns regardless of adapter verification state. The `has_verified_worker_adapter` gate SHALL be removed from the board template.

#### Scenario: No verified adapter exists
- **WHEN** no adapter is verified
- **AND** a task is in the Estimated column
- **THEN** the "Launch task" button is visible

#### Scenario: Launch fails due to unverified adapter
- **WHEN** operator clicks "Launch task" with no verified adapter
- **THEN** the request returns a redirect to `/board?error=...`
- **AND** the board displays an error banner with the launch guardrail failure reasons

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

### Requirement: Blocked column is reserved for workflow blockers
The board SHALL use the Blocked column for workflow or dependency blockers, manual-estimate-required tasks, and hard safety guardrail states, not for recoverable Worker runtime failures on otherwise launchable tasks.

#### Scenario: Operator sees dependency block separately from launch failure
- **WHEN** one task has workflow dependency metadata and another Estimated task has a recent Worker timeout
- **THEN** only the dependency-blocked task appears in the Blocked column
- **AND** the timed-out task remains launchable with inline launch-error copy
