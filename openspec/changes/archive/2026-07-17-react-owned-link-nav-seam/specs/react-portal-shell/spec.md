## MODIFIED Requirements

### Requirement: React shell preserves the full Portal chrome

The React Portal shell SHALL render the full Portal application frame: a top brand bar, a left sidebar with the connected-project list and the Setup, Governance, Planning (only when no projects connected), and Settings groups, a `+ Open local repo` action, a logout form when portal auth is required, and a footer. React-owned routes SHALL share that frame so every canonical Portal route reads as the same product. React SHALL be the sole owner of this frame; no server-rendered template SHALL define it. Sidebar and dashboard links to React-owned canonical routes SHALL navigate in-shell through a shared route-aware link seam that decides client-side versus full-page navigation from the canonical route table; links whose target the React shell does not own SHALL remain ordinary full-page anchors.

#### Scenario: React shell renders the sidebar project list from the shared context helper

- **WHEN** an authenticated operator opens a React-owned route with one or more connected projects
- **THEN** the shell SHALL render a sidebar listing those projects, each with its name, a `Task board` subtitle when the project has tasks or a `No tasks` subtitle when it does not, and a `└ Task board` link under projects that have tasks
- **AND** the project data SHALL come from an authenticated FastAPI JSON endpoint that reuses the existing `portal_template_context` helper
- **AND** the shell SHALL render an empty `No projects` state and a reachable `+ Open local repo` action when no projects are connected

#### Scenario: React shell renders the sidebar navigation groups

- **WHEN** an authenticated operator opens a React-owned route
- **THEN** the shell SHALL render the `Setup` group with a `First-run setup` link, the `Governance` group with in-shell `Dashboard`, `Sessions`, and `Alarms` links, the `Settings` group with in-shell `Control plane model`, `Token budget`, `Projects`, and `Worker adapters` links, and a footer reading `Foreman AI HQ portal · operator-controlled budget governance`
- **AND** the `Setup`, `Governance`, and `Settings` group links and the `+ Open local repo` action SHALL use the shared route-aware link seam so their React-owned targets navigate in-shell
- **AND** the Planning group with a `Task board` link SHALL appear only when no projects are connected, and its bare `/board` shim SHALL remain a full-page navigation

#### Scenario: React shell shows logout when portal auth is required

- **WHEN** an authenticated operator opens a React-owned route while portal auth is required
- **THEN** the shell SHALL render a logout control that posts to `/logout`
- **AND** the shell SHALL NOT render a logout control when portal auth is not required

#### Scenario: Dashboard is the sole active home navigation item

- **WHEN** an authenticated operator opens `/dashboard`
- **THEN** the Dashboard sidebar item SHALL be highlighted as active
- **AND** no project sidebar entry SHALL be highlighted
- **AND** the `+ Open local repo` action SHALL NOT be highlighted

#### Scenario: Active project and board routes are highlighted in the sidebar

- **WHEN** an authenticated operator opens a project workspace or project board at the canonical `/projects/{id}` or `/projects/{id}/board`
- **THEN** the sidebar SHALL highlight the active project's sidebar entry so the operator can tell which project the shell is showing
- **AND** the `└ Task board` sub-link SHALL be highlighted only on the board route, not on the project workspace
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

#### Scenario: React-owned sidebar links navigate in-shell while server-rendered targets stay full-page

- **WHEN** an authenticated operator follows a sidebar link whose canonical target is a React-owned route — a `Settings` group item, `Alarms`, `Sessions`, `First-run setup`, `+ Open local repo` (`/projects`), a project, or its `└ Task board`
- **THEN** the shell SHALL navigate client-side via the shared route-aware link seam without a full-page transition
- **AND** browser Back and Forward SHALL preserve those route transitions
- **WHEN** an authenticated operator follows a sidebar link whose canonical target the React shell does not own — the bare `/board` Planning shim, or the `/login` / `/logout` controls
- **THEN** the shared seam SHALL fall back to an ordinary full-page navigation to that canonical route
- **AND** the seam SHALL derive React ownership from the same canonical route table the router uses, so the two never disagree about which targets stay full-page

#### Scenario: Sidebar navigation endpoint requires portal auth

- **WHEN** an unauthenticated request calls the sidebar navigation JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary
- **AND** an authenticated request SHALL receive `portal_auth_required` and a `sidebar_projects` array whose items include `id`, `name`, and `task_count`
