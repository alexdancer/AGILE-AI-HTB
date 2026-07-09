# react-portal-shell Specification

## Purpose

Define the React/Vite Portal shell contract served by FastAPI, including build-aware fallbacks, authenticated JSON handoff endpoints, migrated project workspace and board surfaces, and client-side navigation for React-owned routes while preserving server-rendered Jinja pages for non-migrated workflows.
## Requirements
### Requirement: FastAPI serves the React Portal shell
The system SHALL serve a built Vite React Portal shell from the existing FastAPI application without introducing a separate Node runtime server.

#### Scenario: Built React shell is available
- **WHEN** an authenticated operator opens a route owned by the React Portal shell after frontend assets have been built
- **THEN** FastAPI SHALL return the React shell `index.html`
- **AND** React asset files SHALL be served from the same FastAPI process

#### Scenario: React assets are missing
- **WHEN** an authenticated operator opens a React-owned route and the built frontend assets are not available
- **THEN** the system SHALL return a clear missing-build response or keep the existing Jinja route available for that surface
- **AND** the response SHALL NOT silently render a broken blank shell

#### Scenario: No separate frontend server is required in production
- **WHEN** AGILE-AI-HTB is served for normal operator use after the React frontend is built
- **THEN** the operator SHALL NOT need to run `vite`, `npm run dev`, or another Node server to use the migrated Portal surface

### Requirement: React owns only the migrated project surfaces
The React Portal shell SHALL own only its project-picker home, selected project workspace, and project board shell while existing Jinja pages remain available for non-migrated surfaces.

#### Scenario: Unknown React paths are not claimed
- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{project_id}`, or `/app/projects/{project_id}/board`
- **THEN** the system SHALL return not found instead of silently rendering the React project-picker home

#### Scenario: Project workspace opens in React shell
- **WHEN** an authenticated operator opens the migrated project workspace route for an existing connected project
- **THEN** the React shell SHALL show project identity, readiness summary, board entry, and actionable project state using data supplied by FastAPI

#### Scenario: Project board opens in React shell
- **WHEN** an authenticated operator opens the migrated project board route for an existing connected project
- **THEN** the React shell SHALL show project-scoped board columns, compact task cards, and queue/run status
- **AND** non-migrated task intake, launch, and review workflows SHALL remain reachable through an ordinary full-page link to the Jinja project board

#### Scenario: Non-migrated pages remain available
- **WHEN** an authenticated operator opens setup, settings, sessions, alarms, dashboard, login, or another non-migrated Portal page
- **THEN** the existing FastAPI/Jinja page SHALL remain reachable unless that page is explicitly migrated by a later change

### Requirement: React uses authenticated JSON handoff endpoints
The React Portal shell SHALL load project workspace and project board state through authenticated FastAPI JSON endpoints that reuse existing view helpers and domain logic.

#### Scenario: Project state requires portal auth
- **WHEN** an unauthenticated request calls a React project workspace or board JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary

#### Scenario: JSON state reuses existing project behavior
- **WHEN** React requests project workspace or project board state for `{project_id}`
- **THEN** FastAPI SHALL derive the response from existing project, board, Worker readiness, budget, run automation, and review evidence helpers where those helpers already exist
- **AND** it SHALL NOT duplicate launch guardrail, estimation, Worker Run, budget, or review-disposition rules in frontend code

#### Scenario: Task actions stay backend-authoritative
- **WHEN** React submits task intake, estimate, launch, refresh, queue, review, archive, dismiss, or block actions
- **THEN** the request SHALL call existing FastAPI action paths or thin JSON wrappers around those paths
- **AND** backend validation SHALL remain authoritative for project binding, launch guardrails, budget acknowledgement, native usage acknowledgement, and review disposition

### Requirement: Frontend build checks are explicit
The system SHALL provide explicit commands or documented checks for building the React frontend and verifying the FastAPI app can serve the built shell.

#### Scenario: Frontend build succeeds
- **WHEN** the frontend build command is run from the repository
- **THEN** it SHALL produce static assets in the directory FastAPI is configured to serve

#### Scenario: Backend test suite covers shell serving
- **WHEN** the repository verification suite runs for this change
- **THEN** it SHALL include a check that FastAPI serves the React shell or reports missing assets clearly

### Requirement: Jinja remains the default authenticated landing
The authenticated Portal landing SHALL use the existing server-rendered
Jinja surface while the React shell lacks Portal chrome, dashboard, and
AGILE Board parity. The React shell SHALL remain reachable at `/app`,
`/app/projects/{id}`, and `/app/projects/{id}/board` as an
experimental/migrated surface, but SHALL NOT
be the default landing for root, login, or logout until a later change
re-enables it after parity gates pass. A missing or partial React build
SHALL never leave the Portal without a usable landing.

#### Scenario: Landing uses the server-rendered Portal when the React build is present
- **WHEN** an authenticated operator opens the Portal root or completes login and the React frontend has been built
- **THEN** the system SHALL send the operator to the existing server-rendered landing (`/projects` or `/projects/{first-connected}`)
- **AND** the system SHALL NOT redirect to `/app` as the default landing

#### Scenario: Landing uses the server-rendered Portal when the build is absent
- **WHEN** an authenticated operator opens the Portal root or completes login and the built React frontend is not available
- **THEN** the system SHALL send the operator to the existing server-rendered landing (`/projects` or `/projects/{first-connected}`)
- **AND** the Portal SHALL remain usable without the React build

#### Scenario: Login still lands on the server-rendered Portal
- **WHEN** an operator successfully logs in while portal auth is required
- **THEN** the existing login flow SHALL set the portal session and redirect to the server-rendered landing
- **AND** no separate React login page SHALL be required by this change

#### Scenario: React shell remains reachable as a non-default surface
- **WHEN** an authenticated operator navigates explicitly to one of the three declared React routes after the frontend has been built
- **THEN** the system SHALL serve the React Portal shell for that route
- **AND** the system SHALL NOT remove or rename those declared routes or their authenticated JSON handoff endpoints as part of this rollback

#### Scenario: Missing or partial React build never renders a blank shell
- **WHEN** an operator navigates explicitly to `/app` and the React build is missing or references unavailable assets
- **THEN** the system SHALL return a clear missing-build response
- **AND** the response SHALL NOT silently render a broken blank shell

### Requirement: React shell provides a project picker home
The React Portal shell SHALL provide a home view that lists the operator's
connected projects with entry points into each project's workspace and board, so
operators reach a project without typing a URL or a project id.

#### Scenario: Home lists connected projects
- **WHEN** an authenticated operator opens the React shell home with one or more connected projects
- **THEN** the shell SHALL list those projects with a way to open each project's React workspace and board

#### Scenario: Home has an actionable empty state
- **WHEN** an authenticated operator opens the React shell home with no connected projects
- **THEN** the shell SHALL show an empty state that links to the existing connect-project flow
- **AND** the home SHALL NOT be a dead end

#### Scenario: Project list uses an authenticated JSON handoff
- **WHEN** the React shell home requests the connected-project list
- **THEN** the system SHALL serve it from an authenticated FastAPI JSON endpoint that reuses existing project-list and task-count helpers
- **AND** an unauthenticated request to that endpoint SHALL be rejected by the existing portal authentication boundary

### Requirement: React shell navigates client-side between its surfaces
The React Portal shell SHALL let operators move between its home, project
workspace, and project board without manual URL entry, while deep links to
React-owned routes still resolve on a full page load.

#### Scenario: Selecting a project opens its workspace in-shell
- **WHEN** an operator selects a project from the React shell home
- **THEN** the shell SHALL open that project's workspace without the operator typing a URL

#### Scenario: Moving between workspace and board stays in-shell
- **WHEN** an operator opens the board from a project workspace and returns
- **THEN** the shell SHALL navigate between those surfaces client-side without requiring a manually entered URL

#### Scenario: Deep links still resolve
- **WHEN** an operator loads or refreshes a React-owned route such as a project workspace or board URL directly
- **THEN** the system SHALL serve the React shell for that route as it does today

### Requirement: React shell preserves the full Portal chrome

The React Portal shell SHALL render the same application frame as the
server-rendered Jinja Portal (`base.html`): a top brand bar, a left sidebar
with the connected-project list and the Setup, Governance, Planning
(only when no projects connected), and Settings groups, a `+ Open local repo`
action, a logout form when portal auth is required, and a footer. React-owned
routes inside `/app` SHALL share that frame so `/app` reads as the same
product, not a separate mini-application.

#### Scenario: React shell renders the sidebar project list from the same source as Jinja

- **WHEN** an authenticated operator opens a React-owned route under `/app` with one or more connected projects
- **THEN** the shell SHALL render a sidebar listing those projects, each with its name, a `Task board` subtitle when the project has tasks or a `No tasks` subtitle when it does not, and a `└ Task board` link under projects that have tasks
- **AND** the project data SHALL come from an authenticated FastAPI JSON endpoint that reuses the same `portal_template_context` helper that feeds the Jinja sidebar
- **AND** the shell SHALL render an empty `No projects` state and a reachable `+ Open local repo` action when no projects are connected

#### Scenario: React shell renders the sidebar navigation groups

- **WHEN** an authenticated operator opens a React-owned route under `/app`
- **THEN** the shell SHALL render the `Setup` group with a `First-run setup` link, the `Governance` group with `Dashboard`, `Sessions`, and `Alarms` links, the `Settings` group with `Control plane model`, `Token budget`, `Projects`, and `Worker adapters` links, and a footer reading `AGILE-AI-HTB portal · operator-controlled budget governance`
- **AND** the Planning group with a `Task board` link SHALL appear only when no projects are connected, matching the Jinja sidebar contract

#### Scenario: React shell shows logout when portal auth is required

- **WHEN** an authenticated operator opens a React-owned route under `/app` while portal auth is required
- **THEN** the shell SHALL render a logout control that posts to `/logout` the same way the Jinja sidebar does
- **AND** the shell SHALL NOT render a logout control when portal auth is not required

#### Scenario: Active project and active route are highlighted in the sidebar

- **WHEN** an authenticated operator opens a project workspace or project board at `/app/projects/{id}` or `/app/projects/{id}/board`
- **THEN** the sidebar SHALL highlight the active project's sidebar entry so the operator can tell which project the shell is showing
- **AND** the `└ Task board` sub-link SHALL be highlighted only on `/app/projects/{id}/board`, not on the project workspace
- **AND** the shell SHALL NOT mark Setup/Governance/Settings group items as active, because those routes are non-migrated full-page Jinja pages whose Jinja sidebar owns active state on full load

#### Scenario: Unknown React paths return not found

- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{id}`, or `/app/projects/{id}/board`
- **THEN** FastAPI SHALL return not found instead of serving the React project-picker home

#### Scenario: Non-migrated Jinja pages remain reachable from the React sidebar via full-page navigation

- **WHEN** an authenticated operator follows a Setup, Governance, Settings, Planning, task-history, or full-board link from the React sidebar
- **THEN** the browser SHALL perform an ordinary full-page navigation to the corresponding Jinja route
- **AND** React-owned routes (`/app`, `/app/projects/{id}`, `/app/projects/{id}/board`) SHALL keep using client-side navigation so in-shell moves do not do a full reload

#### Scenario: Sidebar navigation endpoint requires portal auth

- **WHEN** an unauthenticated request calls the sidebar navigation JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary
- **AND** an authenticated request SHALL receive `portal_auth_required` and a `sidebar_projects` array whose items include `id`, `name`, and `task_count`
