## MODIFIED Requirements

### Requirement: Filter is zero-dependency and client-side only
The board SHALL implement text filtering locally in the rendered client surface. The server-rendered board MAY use inline JavaScript and the React-owned board SHALL use local React client state. No server request or workflow-state change SHALL occur on filter input, and no external library SHALL be required.

#### Scenario: Filter does not trigger network requests
- **WHEN** an operator types in the board filter input on either server-rendered or React-owned board surface
- **THEN** no HTTP requests SHALL be made for each filter keystroke
- **AND** loaded-card visibility changes SHALL happen synchronously in the browser
