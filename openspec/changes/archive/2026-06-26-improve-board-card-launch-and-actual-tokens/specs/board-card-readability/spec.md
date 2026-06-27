## ADDED Requirements

### Requirement: Board cards show actual Worker execution tokens
Board task cards SHALL surface actual Worker execution token totals when authoritative usage has been recorded for the task.

#### Scenario: Review card shows actual tokens
- **WHEN** a task is in Review after a successful Worker Run
- **AND** `task.actual_tokens` is not null
- **THEN** the board card SHALL display the actual token total in the compact metadata line
- **AND** the value SHALL be formatted distinctly from the estimate.

#### Scenario: Done card preserves actual tokens
- **WHEN** an operator marks a Review task Done
- **AND** the task has `actual_tokens` recorded
- **THEN** the Done board card SHALL continue to display the same actual token total.

#### Scenario: Missing actual tokens are not confused with zero
- **WHEN** a task has no recorded actual token total
- **THEN** the board SHALL NOT display a fabricated zero-token total
- **AND** any unavailable state shown for actual tokens SHALL be distinguishable from `0` actual tokens.

### Requirement: Launch details are never blank
Board task cards SHALL NOT render a `Launch` details disclosure with no visible launch/run evidence.

#### Scenario: Launch details render worker run evidence
- **WHEN** a task has launch or Worker Run evidence
- **THEN** the `Launch` details section SHALL show at least one useful evidence field such as selected adapter, selected model, tracking mode, command plan/workdir evidence, return code, blocked reason, launch error, or retryable failure evidence.

#### Scenario: Launch details hidden when no evidence exists
- **WHEN** a task has no launch or Worker Run evidence available
- **THEN** the board card SHALL omit the `Launch` disclosure or show an explicit unavailable message
- **AND** it SHALL NOT render an empty expanded section.
