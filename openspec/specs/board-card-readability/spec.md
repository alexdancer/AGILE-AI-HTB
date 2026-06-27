# board-card-readability Specification

## Purpose

Define how AGILE Board task cards remain compact and scannable while preserving full task, diagnostic, Worker timeline, log, review, and model provenance evidence for operator audit.

## Requirements

### Requirement: Board cards are compact by default
Board task cards SHALL show a compact default view suitable for scanning, including task title, status action, and key model/tokens metadata without rendering the full raw task or diagnostic payload by default.

#### Scenario: Default board card is compact
- **WHEN** an operator opens the AGILE Board page
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
Board task cards SHALL surface the actually launched Worker model as primary evidence when launch metadata exists, and SHALL retain the estimate recommendation as secondary context when it differs.

#### Scenario: Launched and recommended models differ
- **WHEN** `task.metadata.launch_model` exists and differs from `task.recommended_model`
- **THEN** the card SHALL display the launched model first in the model line
- **AND** SHALL also display the recommended model as secondary evidence with clear labeling that it is the estimate recommendation.
- **WHEN** launch evidence is unavailable
- **THEN** the card SHALL display the recommended model as the model value.

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
