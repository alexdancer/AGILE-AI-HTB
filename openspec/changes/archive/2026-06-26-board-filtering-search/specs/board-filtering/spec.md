## ADDED Requirements

### Requirement: Board supports client-side text filtering

The AGILE Board SHALL include a text input above the board columns. As the operator types, task cards SHALL be filtered to show only cards whose visible text content contains the query (case-insensitive). A match count indicator SHALL display the number of visible cards vs total cards. When the filter is empty, all cards SHALL be visible and the indicator SHALL be hidden.

#### Scenario: Filter matches task title

- **WHEN** the board has tasks "Add save command", "Fix auth bug", and "Refactor CLI"
- **AND** the operator types "save" in the filter input
- **THEN** only "Add save command" SHALL be visible
- **AND** the indicator SHALL show "1 of 3 tasks visible"

#### Scenario: Filter matches metadata text

- **WHEN** a task card displays "Model: gpt-5.4-mini" in its metadata line
- **AND** the operator types "gpt-5.4"
- **THEN** that task SHALL remain visible

#### Scenario: Empty filter restores all cards

- **WHEN** the operator has typed a filter query then clears the input
- **THEN** all task cards SHALL become visible
- **AND** the filter indicator SHALL be hidden

#### Scenario: No matching tasks

- **WHEN** the operator types a query that matches zero task cards
- **THEN** the indicator SHALL show "0 of N tasks visible"
- **AND** columns with filtered-out cards SHALL show "No matching tasks"

### Requirement: Filter is zero-dependency and client-side only

The filter SHALL be implemented with inline JavaScript in the board template. No server requests SHALL be made on filter input. No external libraries SHALL be required.

#### Scenario: Filter does not trigger network requests

- **WHEN** the operator types in the filter input
- **THEN** no HTTP requests SHALL be made
- **AND** all card visibility changes SHALL happen synchronously in the browser
