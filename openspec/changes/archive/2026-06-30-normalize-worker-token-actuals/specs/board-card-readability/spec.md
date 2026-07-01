## MODIFIED Requirements

### Requirement: Board cards show actual Worker execution tokens
Board task cards SHALL surface normalized actual Worker execution token totals when authoritative usage has been recorded for the task. Normalized actuals SHALL exclude cache-read/reused-context tokens and include cache-write/cache-creation, fresh input, output, reasoning, and counted unclassified tokens when available.

#### Scenario: Review card shows actual tokens
- **WHEN** a task is in Review after a successful Worker Run
- **AND** `task.actual_tokens` is not null
- **THEN** the board card SHALL display the normalized actual token total in the compact metadata line
- **AND** the value SHALL be formatted distinctly from the estimate
- **AND** cache-read/reused-context tokens SHALL NOT be merged into the displayed actual token total

#### Scenario: Done card preserves actual tokens
- **WHEN** an operator marks a Review task Done
- **AND** the task has `actual_tokens` recorded
- **THEN** the Done board card SHALL continue to display the same normalized actual token total

#### Scenario: Missing actual tokens are not confused with zero
- **WHEN** a task has no recorded actual token total
- **THEN** the board SHALL NOT display a fabricated zero-token total
- **AND** any unavailable state shown for actual tokens SHALL be distinguishable from `0` actual tokens

### Requirement: Board cards explain Worker actual token components
Board task cards SHALL provide a compact explanation of normalized actual Worker execution token composition and separate cache-read/provider-raw evidence when authoritative component evidence exists for the task's Worker Run.

#### Scenario: Review card has cache-heavy actual tokens
- **WHEN** a task is in Review after a successful Worker Run
- **AND** `task.actual_tokens` is populated from Worker execution evidence
- **AND** raw usage evidence contains recognizable fresh input, cache read, cache write/create, output, reasoning, raw total, or cost components
- **THEN** the board card SHALL keep the normalized actual Worker token total visible in the compact metadata
- **AND** the card SHALL provide a concise explanation of fresh input, cache write/create, output, reasoning, cache read/reused context, provider raw total, and cost when available
- **AND** cache-read/reused-context tokens SHALL be labeled separately from normalized actuals
- **AND** the card SHALL NOT merge Agent Review, estimation, task breakdown, or other control-plane spend into the task actual token value

#### Scenario: Done card preserves token component explanation
- **WHEN** an operator marks a reviewed task Done
- **AND** actual Worker token component evidence exists for that task
- **THEN** the Done card SHALL continue to show the normalized actual Worker token total
- **AND** the Done card SHALL keep the component explanation available without requiring raw JSON inspection

#### Scenario: Actual token components are unavailable
- **WHEN** a task has `actual_tokens` but no recognizable token component evidence
- **THEN** the board card SHALL show the actual Worker token total with an unavailable or provider-total-only component label when needed
- **AND** the card SHALL NOT fabricate fresh input, cache, output, reasoning, or cost component values
