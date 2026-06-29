## ADDED Requirements

### Requirement: Board cards provide wider scan space
The AGILE Board SHALL render task cards with a wider default column/card footprint than the cramped prior layout while preserving the existing compact card content, columns, and task actions.

#### Scenario: Board cards use wider columns
- **WHEN** an operator opens the AGILE Board on a viewport that requires horizontal board scrolling
- **THEN** each board column SHALL use a wider minimum width for task cards than the previous cramped default
- **AND** the board SHALL preserve horizontal scrolling rather than wrapping columns into an unreadable narrow stack

#### Scenario: Wider cards keep existing workflow
- **WHEN** the board renders Estimated, Running, Review, Done, and Blocked tasks
- **THEN** the existing board columns remain available
- **AND** the existing launch, refresh, review, done, block, details, and filtering controls remain available
