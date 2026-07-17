# portal-quality-system Specification

## Purpose

Define the durable Portal quality contract for consistent visual primitives, useful empty/blocked states, and responsive operator workflows across React/Vite surfaces with server-rendered recovery pages.
## Requirements
### Requirement: Portal uses shared visual primitives
The Portal SHALL use shared visual primitives for common page structure, cards, buttons, alerts, empty states, metadata rows, and status/toolbars instead of duplicating page-specific inline presentation for those common patterns. React-migrated surfaces SHALL use shared React components or shared CSS tokens for equivalent patterns. The server-rendered recovery surfaces SHALL be exempt: they carry their own self-contained styling by design, because a recovery surface cannot depend on the assets it may have to apologize for.

#### Scenario: Common UI patterns render consistently
- **WHEN** an authenticated operator views dashboard, project workspace, project board, setup, sessions, or alarms pages
- **THEN** common cards, action links, buttons, alert banners, empty states, and metadata rows SHALL use consistent visual treatment
- **AND** those surfaces SHALL draw that treatment from shared React components or shared CSS tokens

#### Scenario: Recovery surfaces stay self-contained
- **WHEN** the login page or the missing-build recovery response renders
- **THEN** it SHALL render without requiring React, Vite, SPA routing, or a Node-based frontend build pipeline
- **AND** it SHALL NOT depend on shared component or token machinery that a broken build could take with it

#### Scenario: Inline styles are not the primary pattern
- **WHEN** a touched React component renders a common visual pattern
- **THEN** the common pattern SHALL be represented by shared classes, shared CSS tokens, or shared components rather than newly duplicated inline style blocks

### Requirement: Portal supports compact text utilities
The Portal SHALL provide shared styling utilities for compact previews of long operator-facing text while preserving access to the full text where the surface owns the evidence.

#### Scenario: Touched surfaces reuse compact text classes
- **WHEN** a touched Portal surface needs to display long task, report, command, project, result, or evidence text as a preview
- **THEN** the surface SHALL use shared classes for line clamping, wrap-anywhere text, or bounded raw blocks instead of adding one-off inline truncation styles

#### Scenario: Full text remains accessible
- **WHEN** compact text utilities hide overflow in a session or report surface
- **THEN** the same page SHALL provide access to the full text through existing content, native disclosure, or a bounded raw evidence section

### Requirement: Portal is React-rendered with server-rendered recovery
The Portal quality baseline SHALL be a React/Vite presentation layer on every operator-facing canonical route, with server-rendered pages retained only as recovery surfaces: the login page and the missing-build response. FastAPI SHALL remain authoritative for auth, persistence, workflow actions, launch guardrails, budget governance, Worker Run evidence, and review disposition.

#### Scenario: Operator-facing routes are React-rendered
- **WHEN** the Portal is installed, served, and the frontend has been built
- **THEN** every canonical operator-facing route SHALL present through the React Portal shell
- **AND** no operator-facing route SHALL depend on a Jinja template other than the login page

#### Scenario: Recovery surfaces render without a frontend build
- **WHEN** the Portal is served while the React build is missing or partial
- **THEN** the login page SHALL remain renderable through the existing FastAPI stack without requiring React, Vite, SPA routing, or a Node-based frontend build pipeline
- **AND** every other canonical route SHALL return the missing-build recovery response, which SHALL itself render without those dependencies

#### Scenario: A frontend build is a normal operating requirement
- **WHEN** an operator serves the Portal for normal use
- **THEN** building the React frontend SHALL be a documented prerequisite rather than an optional enhancement
- **AND** the missing-build recovery response SHALL name the build command

#### Scenario: FastAPI remains authoritative
- **WHEN** a React surface performs any workflow action
- **THEN** FastAPI SHALL remain authoritative for auth, persistence, workflow actions, launch guardrails, budget governance, Worker Run evidence, and review disposition
- **AND** the React client SHALL NOT own those decisions

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
