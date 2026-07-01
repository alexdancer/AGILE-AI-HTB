## ADDED Requirements

### Requirement: Dashboard explains Worker token composition
The Portal SHALL explain cache-inclusive Worker execution spend by showing token component composition when component evidence is available from the token ledger raw usage.

#### Scenario: Worker execution spend includes cache-heavy usage
- **WHEN** the dashboard summarizes current-period token usage
- **AND** Worker execution token rows contain raw usage with fresh input, cache read, cache write/create, output, reasoning, or cost fields
- **THEN** the dashboard SHALL show Worker execution total tokens as the governed budgeted total
- **AND** the dashboard SHALL show a component breakdown that distinguishes fresh input, cache read/reused context, cache write/create, output, reasoning, and cost when present
- **AND** the dashboard SHALL NOT imply that cache read tokens are newly supplied task text

#### Scenario: Component evidence is unavailable
- **WHEN** the dashboard summarizes token rows that do not contain recognizable token component fields
- **THEN** the dashboard SHALL continue showing the authoritative total token usage
- **AND** the dashboard SHALL show that the component breakdown is unavailable rather than fabricating zeros

### Requirement: Dashboard separates completed Worker actuals from failed attempt spend
The Portal SHALL distinguish completed task Worker actuals from failed, retry, or incomplete Worker attempt spend when Worker Run/task status evidence is available.

#### Scenario: Failed Worker attempts spent tokens before completed tasks
- **WHEN** current-period Worker execution token rows include both completed Worker Runs and failed or retryable Worker Runs
- **THEN** the dashboard SHALL include all of those tokens in total governed model spend
- **AND** the dashboard SHALL show completed task Worker actuals separately from failed/retry Worker spend
- **AND** the dashboard SHALL make clear that failed/retry attempt spend can make Worker execution spend exceed the number shown beside reviewable completed tasks

#### Scenario: Attempt status cannot be resolved
- **WHEN** Worker execution token rows cannot be joined to a Worker Run or task status
- **THEN** the dashboard SHALL keep those tokens in governed budget totals
- **AND** the dashboard SHALL label the attempt-status split as unavailable or partially classified

### Requirement: Budget enforcement remains cache-inclusive
Daily budget usage SHALL continue to use total governed model spend, including provider-reported cache read/write tokens and failed/retry attempts, while task actuals and per-session Worker caps remain Worker execution scoped.

#### Scenario: Cache tokens are reported by a Worker provider
- **WHEN** a Worker run records provider-reported cache read or cache write/create tokens
- **THEN** daily governed budget usage SHALL include those cache tokens in the total used value
- **AND** the budget zone SHALL be computed from the cache-inclusive total governed spend and saved daily cap
- **AND** task `actual_tokens` SHALL remain based on Worker execution evidence for the task, not control-plane or Agent Review spend
