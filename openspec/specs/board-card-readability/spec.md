# board-card-readability Specification

## Purpose

Define how Orchestration Board task cards remain compact and scannable while preserving full task, diagnostic, Worker timeline, log, review, and model provenance evidence for operator audit.
## Requirements
### Requirement: Board cards are compact by default
Board task cards SHALL show a compact default view suitable for scanning, including task title, status action, and key model/tokens metadata without rendering the full raw task or diagnostic payload by default.

#### Scenario: Default board card is compact
- **WHEN** an operator opens the Orchestration Board page
- **THEN** each task card SHALL render task text, IDs, model fields, and diagnostic evidence in bounded/summary form
- **AND** full task text and verbose diagnostics SHALL NOT be the only visible content in the card header by default
- **AND** the card SHALL remain fully actionable (Run, Review, Done, Block, etc. buttons and links).

### Requirement: Board card verbose evidence is discoverable on demand
Board task cards SHALL place verbose payloads behind native expandable sections so operators can inspect full evidence only when needed.

#### Scenario: Full task text is moved to expandable evidence
- **WHEN** an operator expands a card's details
- **THEN** full task text SHALL be available in an expandable section
- **AND** verbose sections SHALL include launch diagnostics, Worker timeline entries, stdout/stderr, and review/blocked metadata when present.
- **AND** each expanded region SHALL render long text in bounded/scrollable containers to avoid page breakage.

### Requirement: Board model provenance is explicit and ordered
Board task cards SHALL surface the actually launched Worker model as primary evidence when launch metadata exists, and SHALL retain the routed task model as secondary context when it differs.

#### Scenario: Launched and routed models differ
- **WHEN** `task.metadata.launch_model` exists and differs from `task.recommended_model`
- **THEN** the card SHALL display the launched model first in the model line
- **AND** SHALL also display the routed model as secondary evidence with clear labeling that it is the estimated task's routed Worker model.
- **WHEN** launch evidence is unavailable
- **THEN** the card SHALL display the routed task model as the model value.

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

### Requirement: Launch details are never blank
Board task cards SHALL NOT render a `Launch` details disclosure with no visible launch/run evidence.

#### Scenario: Launch details render worker run evidence
- **WHEN** a task has launch or Worker Run evidence
- **THEN** the `Launch` details section SHALL show at least one useful evidence field such as selected adapter, selected model, tracking mode, command plan/workdir evidence, return code, blocked reason, launch error, or retryable failure evidence.

#### Scenario: Launch details hidden when no evidence exists
- **WHEN** a task has no launch or Worker Run evidence available
- **THEN** the board card SHALL omit the `Launch` disclosure or show an explicit unavailable message
- **AND** it SHALL NOT render an empty expanded section.

### Requirement: Board cards provide wider scan space
The Orchestration Board SHALL render task cards with a wider default column/card footprint than the cramped prior layout while preserving the existing compact card content, columns, and task actions.

#### Scenario: Board cards use wider columns
- **WHEN** an operator opens the Orchestration Board on a viewport that requires horizontal board scrolling
- **THEN** each board column SHALL use a wider minimum width for task cards than the previous cramped default
- **AND** the board SHALL preserve horizontal scrolling rather than wrapping columns into an unreadable narrow stack

#### Scenario: Wider cards keep existing workflow
- **WHEN** the board renders Estimated, Running, Review, Done, and Blocked tasks
- **THEN** the existing board columns remain available
- **AND** the existing launch, refresh, review, done, block, details, and filtering controls remain available

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
