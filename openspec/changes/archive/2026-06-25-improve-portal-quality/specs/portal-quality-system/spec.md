## ADDED Requirements

### Requirement: Portal uses shared visual primitives
The Portal SHALL use shared server-rendered visual primitives for common page structure, cards, buttons, alerts, empty states, metadata rows, and status/toolbars instead of duplicating page-specific inline presentation for those common patterns.

#### Scenario: Common UI patterns render consistently
- **WHEN** an authenticated operator views dashboard, project workspace, project board, setup, sessions, or alarms pages
- **THEN** common cards, action links, buttons, alert banners, empty states, and metadata rows SHALL use consistent visual treatment
- **AND** the implementation SHALL NOT require a frontend build step

#### Scenario: Inline styles are not the primary pattern
- **WHEN** a touched template renders a common visual pattern
- **THEN** the common pattern SHALL be represented by shared classes rather than newly duplicated inline style blocks

### Requirement: Portal remains server-rendered
The Portal quality pass SHALL preserve FastAPI/Jinja server-rendered pages as the source of truth for workflow state.

#### Scenario: No frontend framework is required
- **WHEN** the Portal is installed and served after this change
- **THEN** it SHALL NOT require React, Vite, a SPA router, or a Node-based frontend build pipeline to render the improved pages

#### Scenario: Vanilla JavaScript is local and optional
- **WHEN** a page uses JavaScript for local polish such as form feedback, filtering, or refresh hints
- **THEN** the JavaScript SHALL enhance the server-rendered page without owning route navigation or workflow state

### Requirement: Empty and blocked states explain the next action
Portal pages SHALL present empty, blocked, and unavailable states with concise cause-and-action copy.

#### Scenario: Empty state gives one useful action
- **WHEN** an operator views a page section with no projects, tasks, sessions, alarms, allowed models, or launchable Worker Adapter
- **THEN** the empty state SHALL explain what is missing
- **AND** it SHALL provide one relevant link or action when an existing workflow can fix it

#### Scenario: Blocked state separates cause types
- **WHEN** a workflow is unavailable because of setup, launch guardrails, retryable launch failure, or human Blocked disposition
- **THEN** the Portal SHALL label the state using copy that distinguishes the cause instead of presenting all failures as generic blocked work

### Requirement: Portal remains responsive enough for current surfaces
The Portal SHALL keep board, table, and setup surfaces usable on narrower screens without introducing a separate mobile application.

#### Scenario: Wide content does not break page navigation
- **WHEN** an operator views task board columns or table-heavy pages on a narrow viewport
- **THEN** the page SHALL preserve readable navigation and provide scrolling or stacking behavior for wide content
