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
- **AND** dashboard budget usage uses the saved daily cap when computing the current zone from normalized governed model spend

### Requirement: Token budget distinguishes enforcement from visibility
The Portal SHALL distinguish normalized daily budget enforcement from Worker task actuals and raw provider evidence. Agent Review SHALL count as control-plane orchestration/reporting spend in daily budget usage while remaining separate from Worker execution actuals. Provider cache-read/reused-context tokens SHALL be recorded as raw evidence but excluded from token-budget used values and task actual comparisons.

#### Scenario: Operator reviews budget scope
- **WHEN** the operator views token budget setup
- **THEN** the page explains that the daily budget is enforced against normalized governed model spend from the token ledger
- **AND** the page explains that governed model spend includes control-plane estimation, task breakdown, adapter verification, Agent Review/reporting, Worker execution fresh/cache-write/output/reasoning tokens, and other tracked token rows
- **AND** the page explains that provider cache-read/reused-context tokens are recorded as audit evidence but excluded from budget-used and task-actual comparisons
- **AND** the page explains that per-session Worker execution caps and task `actual_tokens` remain based on Worker execution evidence

#### Scenario: Dashboard summarizes daily budget usage by category
- **WHEN** tracked token usage exists for the current budget period
- **THEN** the budget summary shows normalized governed model spend as the daily budget used value
- **AND** the current budget zone is computed from normalized governed model spend and the saved daily cap
- **AND** the summary shows `worker_execution` usage separately from orchestration/setup/reporting usage
- **AND** Agent Review/reporting tokens are visible as reporting or orchestration spend rather than being hidden under a zero control-plane category
- **AND** provider cache-read/reused-context tokens are shown separately from budget-used totals when evidence exists

#### Scenario: Agent Review spend is budgeted orchestration
- **WHEN** Agent Review records token usage
- **THEN** the token ledger classifies that usage as control-plane orchestration/reporting spend
- **AND** daily budget usage includes the Agent Review tokens except any provider cache-read/reused-context component when reported
- **AND** task Worker execution actuals do not include the Agent Review tokens

#### Scenario: Worker launch checks subtract orchestration spend
- **WHEN** the current budget period already includes control-plane orchestration, Agent Review/reporting, adapter verification, or Worker execution token rows
- **AND** an operator attempts to launch a Worker task
- **THEN** the daily launch budget guardrail subtracts normalized tracked tokens from the saved daily cap before evaluating remaining capacity
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

### Requirement: Dashboard explains Worker token composition
The Portal SHALL explain Worker execution spend by showing normalized actual tokens, cache-read/reused-context evidence, provider raw totals, cost, and token component composition when component evidence is available from the token ledger raw usage.

#### Scenario: Worker execution spend includes cache-heavy usage
- **WHEN** the dashboard summarizes current-period token usage
- **AND** Worker execution token rows contain raw usage with fresh input, cache read, cache write/create, output, reasoning, raw total, or cost fields
- **THEN** the dashboard SHALL show normalized Worker actual tokens excluding cache-read/reused-context tokens
- **AND** the dashboard SHALL show cache-read/reused-context tokens separately from the normalized actual total
- **AND** the dashboard SHALL show provider raw total tokens and cost when present as audit evidence
- **AND** the dashboard SHALL show a component breakdown that distinguishes fresh input, cache read/reused context, cache write/create, output, reasoning, unclassified/provider-total-only, and cost when present
- **AND** the dashboard SHALL NOT imply that cache read tokens are newly supplied task text or budget burn

#### Scenario: Component evidence is unavailable
- **WHEN** the dashboard summarizes token rows that do not contain recognizable token component fields
- **THEN** the dashboard SHALL continue showing the authoritative ledger total as unclassified or provider-total-only evidence
- **AND** the dashboard SHALL show that the component breakdown is unavailable rather than fabricating zeros

### Requirement: Dashboard separates completed Worker actuals from failed attempt spend
The Portal SHALL distinguish completed normalized task Worker actuals from failed, retry, or incomplete normalized Worker attempt spend when Worker Run/task status evidence is available.

#### Scenario: Failed Worker attempts spent tokens before completed tasks
- **WHEN** current-period Worker execution token rows include both completed Worker Runs and failed or retryable Worker Runs
- **THEN** the dashboard SHALL show completed normalized task Worker actuals excluding cache-read/reused-context tokens
- **AND** the dashboard SHALL show failed/retry normalized Worker attempt spend separately
- **AND** the dashboard SHALL keep cache-read/reused-context and provider raw totals visible as evidence separate from those normalized actuals
- **AND** the dashboard SHALL make clear that failed/retry attempt spend can make Worker execution spend exceed the number shown beside reviewable completed tasks

#### Scenario: Attempt status cannot be resolved
- **WHEN** Worker execution token rows cannot be joined to a Worker Run or task status
- **THEN** the dashboard SHALL keep those tokens visible in raw provider or unclassified evidence
- **AND** the dashboard SHALL label the attempt-status split as unavailable or partially classified

### Requirement: Budget enforcement excludes cache reads
Daily budget usage, launch budget guardrails, per-session Worker cap comparisons, and task `actual_tokens` SHALL exclude provider-reported cache-read/reused-context tokens while still recording cache reads as audit evidence. Cache-write/cache-creation tokens SHALL count as normalized Worker actual tokens because they represent newly processed context.

#### Scenario: Cache tokens are reported by a Worker provider
- **WHEN** a Worker run records provider-reported cache read and cache write/create tokens
- **THEN** daily governed budget usage SHALL exclude the cache-read/reused-context tokens from the total used value
- **AND** daily governed budget usage SHALL include fresh input, cache write/create, output, reasoning, and counted unclassified tokens
- **AND** the budget zone SHALL be computed from the normalized governed spend and saved daily cap
- **AND** task `actual_tokens` SHALL use the normalized Worker actual total rather than the provider raw total
- **AND** cache-read/reused-context tokens and provider raw total tokens SHALL remain visible as audit evidence

#### Scenario: Provider exposes only a total without cache components
- **WHEN** a Worker run records provider usage that has a total token count but no recognizable cache-read component
- **THEN** the system SHALL label the usage as unclassified or provider-total-only evidence
- **AND** the system SHALL NOT infer a cache-read exclusion from unavailable fields

### Requirement: Daily budget counter supports soft reset
The Portal SHALL allow an authenticated operator to reset the current day's daily governed budget counter by storing a reset timestamp while preserving all token ledger evidence, session reports, task `actual_tokens`, raw provider evidence, and historical audit views.

#### Scenario: Operator views reset action
- **WHEN** an authenticated operator opens the token budget setup page
- **THEN** the page shows the active daily budget window start used for governed spend calculations
- **AND** the page shows the current-window normalized governed model spend against the saved daily cap
- **AND** the page provides a soft reset action with wording such as "Reset today's budget counter" or "Start new daily budget window"
- **AND** the page explains that reset does not delete token ledger rows, change task actuals, or alter session reports

#### Scenario: Operator resets today's budget counter
- **WHEN** the operator submits the daily budget counter reset action
- **THEN** the system persists the reset timestamp as the active daily budget waterline
- **AND** subsequent daily budget usage is calculated from the later of local-day start and the reset timestamp
- **AND** token ledger rows created before the reset timestamp remain stored and visible in historical/audit views
- **AND** task `actual_tokens` and per-session Worker execution totals remain unchanged

#### Scenario: Reset affects launch guardrails consistently
- **WHEN** a daily budget reset timestamp exists for the current local day
- **AND** an operator attempts to launch a Worker task
- **THEN** the daily launch budget guardrail subtracts normalized governed spend recorded after the active budget waterline from the saved daily cap
- **AND** the per-session Worker execution guardrail continues to evaluate the task's Worker execution estimate against the per-session cap
- **AND** launch budget override metadata uses the same active budget window shown on the Token budget page

#### Scenario: Reset affects dashboard and budget alarms consistently
- **WHEN** a daily budget reset timestamp exists for the current local day
- **THEN** the dashboard daily governed budget value and budget zone are calculated from normalized governed spend recorded after the active budget waterline
- **AND** budget alarms use the same active budget window for daily budget comparisons
- **AND** orchestration, reporting, adapter verification, and Worker execution tokens before the waterline remain available as historical evidence but do not consume the reset daily counter

#### Scenario: New local day supersedes previous reset
- **WHEN** the stored reset timestamp is earlier than the current local-day start
- **THEN** the active daily budget window starts at the current local-day start
- **AND** the previous day's reset timestamp does not reduce or extend the new day's daily budget counter

### Requirement: Budget setup state has an authenticated JSON read
The Portal SHALL expose the current token budget setup state through an authenticated JSON read that reuses the existing effective-budget computation, so an authenticated operator surface can display caps and today's counter without recomputing budget rules or reading `guardrails.yaml` directly.

#### Scenario: Budget state read requires authentication
- **WHEN** an unauthenticated caller requests the budget setup state read while portal auth is required
- **THEN** the Portal SHALL reject the request using the existing Portal authentication boundary
- **AND** SHALL NOT return budget setup state

#### Scenario: Budget state read reuses authoritative computation
- **WHEN** an authenticated caller requests the budget setup state read
- **THEN** the response SHALL be derived from the same effective-budget computation used by the existing budget surface
- **AND** it SHALL report the daily governed cap, per-session Worker cap, current-window used and remaining tokens, `budget_since`, and last daily-usage reset timestamp
- **AND** absent cap or counter values SHALL be reported as typed `null` rather than fabricated zeros

### Requirement: Budget save and reset actions offer a sanitized negotiated outcome
The token budget save action and the daily-counter reset action SHALL offer a sanitized, content-negotiated JSON outcome to non-HTML callers while preserving the existing HTML redirect behavior for browser form callers. Cap validation and the soft-reset evidence-preservation guarantees SHALL remain authoritative for both caller types.

#### Scenario: Non-HTML save returns a sanitized outcome
- **WHEN** a caller negotiating `application/json` submits valid caps to the budget save action
- **THEN** the Portal SHALL persist the budget using the existing authoritative save behavior
- **AND** SHALL return a bounded JSON outcome carrying the saved authoritative state
- **AND** SHALL NOT redirect that caller to `/setup`

#### Scenario: Non-HTML save rejects invalid caps without leaking internals
- **WHEN** a caller negotiating `application/json` submits an invalid or non-positive cap value
- **THEN** the Portal SHALL return a sanitized error outcome envelope
- **AND** raw exception or stack detail SHALL NOT appear in the outcome
- **AND** the persisted budget SHALL remain unchanged

#### Scenario: Non-HTML reset returns a sanitized outcome and preserves evidence
- **WHEN** a caller negotiating `application/json` submits the daily-counter reset action
- **THEN** the Portal SHALL reset the daily counter using the existing soft-reset behavior
- **AND** all token ledger evidence, session reports, task `actual_tokens`, raw provider evidence, and historical audit views SHALL remain preserved
- **AND** the Portal SHALL return a bounded JSON outcome carrying the refreshed counter state

#### Scenario: HTML form callers keep existing redirects
- **WHEN** a browser form caller submits the save or reset action without negotiating `application/json`
- **THEN** the Portal SHALL preserve the existing redirect behavior for that action
- **AND** the negotiated JSON path SHALL NOT change the HTML caller experience

