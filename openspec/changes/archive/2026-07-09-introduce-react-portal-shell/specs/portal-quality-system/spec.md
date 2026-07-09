## MODIFIED Requirements

### Requirement: Portal uses shared visual primitives
The Portal SHALL use shared visual primitives for common page structure, cards, buttons, alerts, empty states, metadata rows, and status/toolbars instead of duplicating page-specific inline presentation for those common patterns. Server-rendered pages SHALL continue using shared classes; React-migrated surfaces SHALL use shared React components or shared CSS tokens for equivalent patterns.

#### Scenario: Common UI patterns render consistently
- **WHEN** an authenticated operator views dashboard, project workspace, project board, setup, sessions, or alarms pages
- **THEN** common cards, action links, buttons, alert banners, empty states, and metadata rows SHALL use consistent visual treatment
- **AND** pages that remain server-rendered SHALL NOT require a frontend build step

#### Scenario: Inline styles are not the primary pattern
- **WHEN** a touched template or React component renders a common visual pattern
- **THEN** the common pattern SHALL be represented by shared classes, shared CSS tokens, or shared components rather than newly duplicated inline style blocks

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
