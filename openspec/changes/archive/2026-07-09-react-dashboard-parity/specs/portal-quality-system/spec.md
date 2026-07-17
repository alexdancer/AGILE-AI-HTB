## MODIFIED Requirements

### Requirement: Portal supports compact text utilities
The Portal SHALL provide shared styling utilities for compact previews of long operator-facing text while preserving access to the full text where the page owns the evidence.

#### Scenario: Touched templates reuse compact text classes
- **WHEN** a touched Portal template needs to display long task, report, command, project, result, or evidence text as a preview
- **THEN** the template SHALL use shared classes for line clamping, wrap-anywhere text, or bounded raw blocks instead of adding one-off inline truncation styles

#### Scenario: Full text remains accessible
- **WHEN** compact text utilities hide overflow in a session or report surface
- **THEN** the same page SHALL provide access to the full text through existing content, native disclosure, or a bounded raw evidence section

#### Scenario: Non-migrated pages require no frontend build step
- **WHEN** the compact session report change is implemented
- **THEN** its non-migrated FastAPI/Jinja pages SHALL remain renderable without requiring React, Vite, SPA routing, or a Node-based frontend build pipeline
- **AND** explicitly migrated Portal surfaces MAY use React/Vite assets only when an accepted OpenSpec change scopes that client-side rendering

### Requirement: Portal remains server-rendered
The Portal quality baseline SHALL preserve FastAPI/Jinja server-rendered pages for non-migrated surfaces and as fallback for explicitly migrated React/Vite Portal surfaces.

#### Scenario: No frontend framework is required for Jinja fallback and non-migrated pages
- **WHEN** the Portal is installed and served after this change
- **THEN** the Jinja dashboard fallback, setup, settings, sessions, alarms, login, and other non-migrated pages SHALL remain renderable through the existing FastAPI/Jinja stack without requiring React, Vite, SPA routing, or a Node-based frontend build pipeline

#### Scenario: React-migrated pages may own route rendering
- **WHEN** a page is explicitly migrated into the React Portal shell by an accepted OpenSpec change
- **THEN** that migrated page MAY use React, Vite-built assets, and client-side route rendering for its presentation layer
- **AND** FastAPI SHALL remain authoritative for auth, persistence, workflow actions, launch guardrails, budget governance, Worker Run evidence, and review disposition

#### Scenario: Vanilla JavaScript remains local and optional on server-rendered pages
- **WHEN** a server-rendered page uses JavaScript for local polish such as form feedback, filtering, or refresh hints
- **THEN** the JavaScript SHALL enhance the server-rendered page without owning route navigation or workflow state.