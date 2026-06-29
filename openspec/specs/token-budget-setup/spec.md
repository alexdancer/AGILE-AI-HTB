# token-budget-setup

## Purpose

Define the portal-managed token budget setup flow so operators can configure Worker execution budgets from the UI, understand enforcement scope, and include budget confirmation in first-run readiness.
## Requirements
### Requirement: Portal exposes token budget setup
The Portal SHALL provide a token budget setup surface that lets an operator configure the daily governed model-spend budget and per-session Worker execution budget without editing `guardrails.yaml` by hand.

#### Scenario: Operator views token budget setup
- **WHEN** an authenticated operator opens the token budget setup page
- **THEN** the page shows the current daily token cap for governed model spend
- **AND** the page shows the current per-session Worker execution token cap
- **AND** the page explains that the daily budget is used by launch guardrails and budget alarms

#### Scenario: Operator saves token budget values
- **WHEN** the operator submits valid daily and per-session token caps
- **THEN** the portal persists the budget values used by subsequent sessions and launches
- **AND** the page confirms the saved values
- **AND** dashboard budget usage uses the saved daily cap when computing the current zone from total governed model spend

### Requirement: Token budget distinguishes enforcement from visibility
The Portal SHALL distinguish total daily budget enforcement from Worker task actuals. Agent Review SHALL count as control-plane orchestration/reporting spend in daily budget usage while remaining separate from Worker execution actuals.

#### Scenario: Operator reviews budget scope
- **WHEN** the operator views token budget setup
- **THEN** the page explains that the daily budget is enforced against total governed model spend from the token ledger
- **AND** the page explains that governed model spend includes control-plane estimation, task breakdown, adapter verification, Agent Review/reporting, Worker execution, and other tracked token rows
- **AND** the page explains that per-session Worker execution caps and task `actual_tokens` remain based on Worker execution evidence

#### Scenario: Dashboard summarizes daily budget usage by category
- **WHEN** tracked token usage exists for the current budget period
- **THEN** the budget summary shows total governed model spend as the daily budget used value
- **AND** the current budget zone is computed from total governed model spend and the saved daily cap
- **AND** the summary shows `worker_execution` usage separately from orchestration/setup/reporting usage
- **AND** Agent Review/reporting tokens are visible as reporting or orchestration spend rather than being hidden under a zero control-plane category

#### Scenario: Agent Review spend is budgeted orchestration
- **WHEN** Agent Review records token usage
- **THEN** the token ledger classifies that usage as control-plane orchestration/reporting spend
- **AND** daily budget usage includes the Agent Review tokens
- **AND** task Worker execution actuals do not include the Agent Review tokens

#### Scenario: Worker launch checks subtract orchestration spend
- **WHEN** the current budget period already includes control-plane orchestration, Agent Review/reporting, adapter verification, or Worker execution token rows
- **AND** an operator attempts to launch a Worker task
- **THEN** the daily launch budget guardrail subtracts those tracked tokens from the saved daily cap before evaluating remaining capacity
- **AND** the per-session Worker execution guardrail still evaluates the task's Worker execution estimate against the per-session cap

### Requirement: Budget setup participates in first-run readiness
The Portal SHALL treat token budget setup as part of the first-run launch readiness flow.

#### Scenario: Budget has not been confirmed
- **WHEN** an operator opens the setup overview
- **AND** the token budget has not been confirmed in the portal
- **THEN** the setup checklist shows budget setup as incomplete
- **AND** the checklist links to the token budget setup page

#### Scenario: Budget has been confirmed
- **WHEN** the operator saves token budget settings
- **THEN** the setup overview shows token budget setup as complete
- **AND** Worker launch readiness can proceed to project and Worker verification gates

