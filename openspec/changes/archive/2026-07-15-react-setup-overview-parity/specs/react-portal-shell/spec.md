## ADDED Requirements

### Requirement: React Setup Overview JSON is authenticated, exact, and bounded
FastAPI SHALL expose a new authenticated JSON handoff for Setup Overview that requires Portal authentication and reuses the existing control-plane setup state, effective budget settings, Worker adapter view models with active-adapter selection, Local Runner project capability evaluation, and next-setup-step derivation. The response SHALL be bounded and sanitized so the frontend can render the readiness steps, launch readiness, the next action, and the active Worker adapter without recomputing setup rules in the browser.

#### Scenario: Setup Overview handoff requires authentication
- **WHEN** an unauthenticated caller requests the authenticated React Setup Overview JSON handoff while portal auth is required
- **THEN** FastAPI SHALL reject the request using the Portal authentication boundary
- **AND** SHALL NOT return Setup Overview data, including readiness state or adapter configuration

#### Scenario: Setup Overview JSON is bounded and exact
- **WHEN** an authenticated caller requests the React Setup Overview JSON handoff
- **THEN** the response SHALL include the four readiness steps with name, state, href, and detail, the `ready_to_launch` flag, the next action with label, href, and detail, and the active Worker adapter projection
- **AND** absent optional values SHALL be typed `null` rather than fabricated defaults

#### Scenario: Setup Overview readiness is computed by the backend
- **WHEN** the Setup Overview JSON handoff builds its response
- **THEN** it SHALL reuse the existing control-plane setup state, budget confirmation, active-adapter launchability, project capability evaluation, and next-setup-step derivation that power the Jinja setup page
- **AND** the frontend SHALL render the returned steps and next action rather than deriving readiness from their parts

#### Scenario: Setup Overview adapter projection is allow-listed
- **WHEN** the Setup Overview JSON handoff serializes the active Worker adapter
- **THEN** the response SHALL carry only the adapter name, verification status, launchability, and tracking mode
- **AND** it SHALL NOT serialize the full Worker verification evidence

#### Scenario: Setup Overview reports launch readiness only with a launch-ready project
- **WHEN** the Setup Overview JSON handoff builds its response while the control plane, token budget, and Worker adapter requirements pass but no Connected Project is launch-ready
- **THEN** `ready_to_launch` SHALL be false
- **AND** the projects step state SHALL NOT report ready

### Requirement: React Setup Overview navigates inside the shell
React SHALL render Setup Overview inside the shared Portal chrome on the canonical `/setup` URL when the complete build is available, and FastAPI SHALL render the existing Jinja page at the same URL when the build is missing or partial. The view SHALL preserve the next-action toolbar, the four readiness cards with their destination links, the launch-readiness panel, and the active Worker adapter panel. The Setup sidebar link SHALL use in-shell client navigation.

#### Scenario: Built canonical route opens React Setup Overview in-shell
- **WHEN** an authenticated operator opens `/setup` while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell and render Setup Overview inside the full Portal chrome
- **AND** React SHALL request the authenticated Setup Overview JSON for its readiness steps, next action, and active adapter

#### Scenario: Missing or partial build keeps canonical Setup Overview in Jinja
- **WHEN** an authenticated operator opens `/setup` while the React build is missing or partial
- **THEN** FastAPI SHALL render the existing Jinja setup page at the same canonical URL
- **AND** it SHALL NOT return a blank shell or require an alternate fallback URL

#### Scenario: Setup adapter context is bookmarkable
- **WHEN** an authenticated operator opens `/setup` with an `adapter_id` query parameter while the complete React build is available
- **THEN** React SHALL pass that `adapter_id` through to the Setup Overview JSON handoff
- **AND** the backend SHALL perform active-adapter selection using its existing selection rule, including its existing fallback when the `adapter_id` is absent or unknown
- **AND** React SHALL NOT select the active adapter itself or hold the selection as client-only state

#### Scenario: Setup forwards adapter context to Worker Settings
- **WHEN** an operator opens the Worker adapter destination from the React Setup Overview while an `adapter_id` is in effect
- **THEN** the destination link SHALL carry that `adapter_id` so Worker Settings opens the same adapter
- **AND** the operator SHALL NOT be returned to the default adapter

#### Scenario: Setup Overview load failure is sanitized
- **WHEN** the React Setup Overview cannot load its state
- **THEN** React SHALL render a fixed sanitized message with a retry path, and a sign-in message when the failure is an authentication rejection
- **AND** it SHALL NOT render the underlying error text into the page

#### Scenario: Both renderers read one tracking source
- **WHEN** the React Setup Overview and the Jinja fallback render the tracking of the same active Worker adapter
- **THEN** both SHALL read the tracking mode from the Worker adapter view model rather than from raw verification evidence
- **AND** an adapter whose tracking has not been verified SHALL render as unverified on both surfaces

## MODIFIED Requirements

### Requirement: React is the build-aware default authenticated landing
The normal Portal landing SHALL use the React dashboard at `/app` when the complete built React shell is available. The system SHALL validate the React index and all referenced local React assets before choosing `/app`; when that validation fails, the normal landing SHALL remain the existing server-rendered first-project or `/projects` route. This promotion SHALL NOT remove explicit Jinja fallback routes. React route ownership SHALL include `/app`, `/app/projects/{id}`, `/app/projects/{id}/board`, `/sessions`, `/sessions/{session_id}`, `/task-breakdowns/{breakdown_id}/review`, `/setup`, and the destination Settings routes `/settings/control-plane`, `/settings/budget`, `/settings/project`, and `/settings/workers` only for the migrated surfaces defined by this specification.

#### Scenario: Auth-disabled local root opens built React dashboard
- **WHEN** portal auth is not required and an operator opens `/` while the complete React build is available
- **THEN** the system SHALL redirect to `/app`
- **AND** the React shell SHALL render its dashboard inside the full Portal chrome

#### Scenario: Successful login opens built React dashboard
- **WHEN** portal auth is required and an operator submits a valid portal token while the complete React build is available
- **THEN** the system SHALL preserve the existing signed cookie behavior
- **AND** the successful login response SHALL redirect to `/app`

#### Scenario: Authenticated root opens built React dashboard
- **WHEN** portal auth is required and an authenticated operator opens `/` while the complete React build is available
- **THEN** the system SHALL redirect to `/app`

#### Scenario: Unauthenticated shared root still requires login
- **WHEN** portal auth is required and an unauthenticated operator opens `/`
- **THEN** the system SHALL redirect to `/login`
- **AND** build availability SHALL NOT bypass the existing authentication boundary

#### Scenario: Auth-disabled login and logout use normal landing
- **WHEN** portal auth is not required and an operator opens `/login`, submits a well-formed `/login` request containing the existing required token form field, or submits `/logout`
- **THEN** the system SHALL preserve existing harmless login/logout behavior
- **AND** it SHALL redirect to `/app` when the complete React build is available

#### Scenario: Missing React index falls back to Jinja landing
- **WHEN** a normal landing decision occurs and the React index is missing
- **THEN** the system SHALL redirect to the existing server-rendered first-project route when a connected project exists, otherwise `/projects`
- **AND** the operator SHALL NOT receive a blank shell or missing-build `503` as the default landing

#### Scenario: Partial React build falls back to Jinja landing
- **WHEN** the React index exists but one or more referenced local React assets are missing or invalid
- **THEN** the normal landing SHALL use the existing server-rendered first-project or `/projects` route
- **AND** the system SHALL NOT promote the partial shell

#### Scenario: Explicit React deep link retains clear missing-build behavior
- **WHEN** an authenticated operator explicitly opens a declared `/app` route while the React build is unavailable or partial
- **THEN** the existing clear missing-build response SHALL remain available
- **AND** the response SHALL provide a usable Jinja fallback link rather than a blank shell

#### Scenario: Missing or partial build keeps canonical Sessions in Jinja
- **WHEN** an authenticated operator opens `/sessions` or `/sessions/{session_id}` while the React build is missing or partial
- **THEN** FastAPI SHALL render the corresponding existing Jinja surface at the same canonical URL
- **AND** it SHALL NOT return a blank shell or require an alternate fallback URL

#### Scenario: Missing or partial build keeps canonical Task Breakdown Review in Jinja
- **WHEN** an authenticated operator opens `/task-breakdowns/{breakdown_id}/review` while the React build is missing or partial
- **THEN** FastAPI SHALL render the existing Jinja review at the same canonical URL
- **AND** it SHALL preserve Accept, Retry, Manual Candidate, Cancel, and Session Report links

#### Scenario: Non-migrated and fallback Jinja routes remain reachable
- **WHEN** an operator on the default React shell follows a link to Alarms, Settings, task history, or an explicit server-rendered fallback surface
- **THEN** the existing FastAPI/Jinja route SHALL remain reachable through ordinary full-page navigation, serving the Jinja page directly for non-migrated surfaces and as the missing/partial-build fallback for migrated canonical routes
- **AND** no React client route SHALL claim a path that this specification has not migrated

### Requirement: React shell preserves the full Portal chrome

The React Portal shell SHALL render the same application frame as the server-rendered Jinja Portal (`base.html`): a top brand bar, a left sidebar with the connected-project list and the Setup, Governance, Planning (only when no projects connected), and Settings groups, a `+ Open local repo` action, a logout form when portal auth is required, and a footer. React-owned routes SHALL share that frame so migrated canonical Sessions routes read as the same product, not a separate mini-application.

#### Scenario: React shell renders the sidebar project list from the same source as Jinja

- **WHEN** an authenticated operator opens a React-owned route with one or more connected projects
- **THEN** the shell SHALL render a sidebar listing those projects, each with its name, a `Task board` subtitle when the project has tasks or a `No tasks` subtitle when it does not, and a `└ Task board` link under projects that have tasks
- **AND** the project data SHALL come from an authenticated FastAPI JSON endpoint that reuses the same `portal_template_context` helper that feeds the Jinja sidebar
- **AND** the shell SHALL render an empty `No projects` state and a reachable `+ Open local repo` action when no projects are connected

#### Scenario: React shell renders the sidebar navigation groups

- **WHEN** an authenticated operator opens a React-owned route
- **THEN** the shell SHALL render the `Setup` group with a `First-run setup` link, the `Governance` group with an in-shell `Dashboard` link plus `Sessions` and full-page `Alarms` links, the `Settings` group with `Control plane model`, `Token budget`, `Projects`, and `Worker adapters` links, and a footer reading `Foreman AI HQ portal · operator-controlled budget governance`
- **AND** the Planning group with a `Task board` link SHALL appear only when no projects are connected, matching the Jinja sidebar contract

#### Scenario: React shell shows logout when portal auth is required

- **WHEN** an authenticated operator opens a React-owned route while portal auth is required
- **THEN** the shell SHALL render a logout control that posts to `/logout` the same way the Jinja sidebar does
- **AND** the shell SHALL NOT render a logout control when portal auth is not required

#### Scenario: Dashboard is the sole active home navigation item

- **WHEN** an authenticated operator opens `/app`
- **THEN** the Dashboard sidebar item SHALL be highlighted as active
- **AND** no project sidebar entry SHALL be highlighted
- **AND** the `+ Open local repo` action SHALL NOT be highlighted

#### Scenario: Active project and board routes are highlighted in the sidebar

- **WHEN** an authenticated operator opens a project workspace or project board at `/app/projects/{id}` or `/app/projects/{id}/board`
- **THEN** the sidebar SHALL highlight the active project's sidebar entry so the operator can tell which project the shell is showing
- **AND** the `└ Task board` sub-link SHALL be highlighted only on `/app/projects/{id}/board`, not on the project workspace
- **AND** the Dashboard sidebar item SHALL NOT be highlighted
- **AND** the shell SHALL NOT mark Setup, Sessions, Alarms, or Settings group items as active

#### Scenario: Sessions routes are highlighted in the sidebar

- **WHEN** an authenticated operator opens `/sessions` or `/sessions/{session_id}` with a complete React build
- **THEN** the Sessions sidebar item SHALL be highlighted
- **AND** no Dashboard or project sidebar entry SHALL be highlighted

#### Scenario: React-owned Settings routes are highlighted in the sidebar

- **WHEN** an authenticated operator opens `/settings/control-plane`, `/settings/budget`, `/settings/project`, or `/settings/workers` with a complete React build
- **THEN** the shell SHALL highlight that route's `Settings` group sidebar item as active
- **AND** no Dashboard or project sidebar entry SHALL be highlighted
- **AND** the shell SHALL highlight at most one `Settings` group item

#### Scenario: Setup route is highlighted in the sidebar

- **WHEN** an authenticated operator opens `/setup` with a complete React build
- **THEN** the shell SHALL highlight the `Setup` group `First-run setup` item as active
- **AND** no Dashboard, project, Sessions, or Settings sidebar entry SHALL be highlighted

#### Scenario: Unknown React paths return not found

- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{id}`, or `/app/projects/{id}/board`
- **THEN** FastAPI SHALL return not found instead of serving a React surface

#### Scenario: Non-migrated Jinja pages remain reachable from the React sidebar via full-page navigation

- **WHEN** an authenticated operator follows an Alarms, Settings, Planning, task-history, or full-board link from the React sidebar
- **THEN** the browser SHALL perform an ordinary full-page navigation to the corresponding canonical route rather than an in-shell transition
- **AND** the shell's own in-shell surfaces SHALL use client-side navigation so in-shell moves do not require a full reload

#### Scenario: Sidebar navigation endpoint requires portal auth

- **WHEN** an unauthenticated request calls the sidebar navigation JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary
- **AND** an authenticated request SHALL receive `portal_auth_required` and a `sidebar_projects` array whose items include `id`, `name`, and `task_count`
