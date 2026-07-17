## MODIFIED Requirements

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

## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Portal remains server-rendered
**Reason**: The requirement preserved "FastAPI/Jinja server-rendered pages for non-migrated surfaces and as fallback for explicitly migrated React/Vite Portal surfaces." After slices 1–11b there are no non-migrated surfaces left, and this change deletes the fallback. Its scenario "No frontend framework is required for Jinja fallback and non-migrated pages" enumerates the dashboard fallback, setup, settings, sessions, and alarms pages that this change removes — a list that is accurate at HEAD and false once the templates are deleted, which is why it must change in this same diff rather than before or after it. Its scenario "Vanilla JavaScript remains local and optional on server-rendered pages" governed pages that no longer exist; the surviving login page carries no JavaScript at all, by explicit decision in the standalone-portal-recovery-login change.

**Migration**: Replaced by "Portal is React-rendered with server-rendered recovery", which keeps the FastAPI-authority guarantee and the no-build-required guarantee verbatim in substance, but scopes the latter to the recovery surfaces that still need it. Operators who relied on running the Portal without a Node toolchain must now build the frontend once; `npm run build` is an existing documented gate, and `/login` plus the recovery response keep working without it. The scenario "React-migrated pages may own route rendering" is subsumed: React now owns every operator-facing route by default rather than by per-change exception.
