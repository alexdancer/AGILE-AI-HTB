# board-card-readability Specification

## ADDED Requirements

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