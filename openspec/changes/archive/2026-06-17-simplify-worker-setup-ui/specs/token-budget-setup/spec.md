## ADDED Requirements

### Requirement: Portal exposes token budget setup

The Portal SHALL provide a token budget setup surface that lets an operator configure the daily token budget and per-session token budget without editing `guardrails.yaml` by hand.

#### Scenario: Operator views token budget setup

- **WHEN** an authenticated operator opens the token budget setup page
- **THEN** the page shows the current daily token cap
- **AND** the page shows the current per-session token cap
- **AND** the page explains that these budgets are used by launch guardrails and budget alarms

#### Scenario: Operator saves token budget values

- **WHEN** the operator submits valid daily and per-session token caps
- **THEN** the portal persists the budget values used by subsequent sessions and launches
- **AND** the page confirms the saved values
- **AND** dashboard budget usage uses the saved daily cap when computing the current zone

### Requirement: Token budget distinguishes enforcement from visibility

The Portal SHALL distinguish Worker budget enforcement from total tracked spend visibility.

#### Scenario: Operator reviews budget scope

- **WHEN** the operator views token budget setup
- **THEN** the page explains that Worker launch budget enforcement is based on `worker_execution` spend
- **AND** the page explains that dashboard visibility may include control-plane, task breakdown, adapter verification, reporting, and Worker execution spend

#### Scenario: Dashboard summarizes budget usage by category

- **WHEN** tracked token usage exists for the current budget period
- **THEN** the budget summary shows `worker_execution` usage separately from orchestration/setup usage
- **AND** the summary shows total tracked usage for visibility

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
