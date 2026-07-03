## ADDED Requirements

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
