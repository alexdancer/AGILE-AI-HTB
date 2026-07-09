# portal-quality-system Specification

## Purpose

Define the durable server-rendered Portal quality contract for consistent visual primitives, useful empty/blocked states, and responsive operator workflows without introducing a frontend build pipeline.
## Requirements
### Requirement: Portal uses shared visual primitives
The Portal SHALL use shared visual primitives for common page structure, cards, buttons, alerts, empty states, metadata rows, and status/toolbars instead of duplicating page-specific inline presentation for those common patterns. Server-rendered pages SHALL continue using shared classes; React-migrated surfaces SHALL use shared React components or shared CSS tokens for equivalent patterns.

#### Scenario: Common UI patterns render consistently
- **WHEN** an authenticated operator views dashboard, project workspace, project board, setup, sessions, or alarms pages
- **THEN** common cards, action links, buttons, alert banners, empty states, and metadata rows SHALL use consistent visual treatment
- **AND** pages that remain server-rendered SHALL NOT require a frontend build step

#### Scenario: Inline styles are not the primary pattern
- **WHEN** a touched template or React component renders a common visual pattern
- **THEN** the common pattern SHALL be represented by shared classes, shared CSS tokens, or shared components rather than newly duplicated inline style blocks

### Requirement: Portal supports compact text utilities
The Portal SHALL provide shared server-rendered styling utilities for compact previews of long operator-facing text while preserving access to the full text where the page owns the evidence.

#### Scenario: Touched templates reuse compact text classes
- **WHEN** a touched Portal template needs to display long task, report, command, project, result, or evidence text as a preview
- **THEN** the template SHALL use shared classes for line clamping, wrap-anywhere text, or bounded raw blocks instead of adding one-off inline truncation styles

#### Scenario: Full text remains accessible
- **WHEN** compact text utilities hide overflow in a session or report surface
- **THEN** the same page SHALL provide access to the full text through existing content, native disclosure, or a bounded raw evidence section

#### Scenario: No frontend build step is introduced
- **WHEN** the compact session report change is implemented
- **THEN** the Portal SHALL remain renderable through the existing FastAPI/Jinja server-rendered stack without React, Vite, SPA routing, or a Node-based frontend build pipeline

### Requirement: Portal remains server-rendered
The Portal quality baseline SHALL preserve FastAPI/Jinja server-rendered pages for non-migrated surfaces while allowing explicitly scoped React/Vite Portal surfaces to own their client-side rendering during frontend migration.

#### Scenario: No frontend framework is required for non-migrated pages
- **WHEN** the Portal is installed and served after this change
- **THEN** dashboard, setup, settings, sessions, alarms, login, and other non-migrated pages SHALL remain renderable through the existing FastAPI/Jinja stack without requiring React, Vite, SPA routing, or a Node-based frontend build pipeline

#### Scenario: React-migrated pages may own route rendering
- **WHEN** a page is explicitly migrated into the React Portal shell by an accepted OpenSpec change
- **THEN** that migrated page MAY use React, Vite-built assets, and client-side route rendering for its presentation layer
- **AND** FastAPI SHALL remain authoritative for auth, persistence, workflow actions, launch guardrails, budget governance, Worker Run evidence, and review disposition

#### Scenario: Vanilla JavaScript remains local and optional on server-rendered pages
- **WHEN** a server-rendered page uses JavaScript for local polish such as form feedback, filtering, or refresh hints
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
