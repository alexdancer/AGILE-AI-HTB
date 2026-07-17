## ADDED Requirements

### Requirement: React shell provides a dashboard home
The React Portal shell SHALL render a dashboard-equivalent home at `/app` for an authenticated operator who explicitly opens the React surface. The dashboard SHALL present operator next actions, daily governed budget, Worker execution tokens, open/critical alarm counts, budget spend breakdown and token component details, active sessions, recent open alarms, estimation accuracy when available, and connected-project entry cards.

#### Scenario: Explicit React home shows dashboard data
- **WHEN** an authenticated operator opens `/app` after React assets are built
- **THEN** the shell SHALL render the React dashboard inside the shared Portal chrome
- **AND** it SHALL load dashboard state from an authenticated FastAPI JSON handoff

#### Scenario: Dashboard retains project entry
- **WHEN** the dashboard has connected projects
- **THEN** it SHALL provide entry points to each project's existing React workspace and board routes
- **AND** it SHALL NOT require a new `/app/projects` route

#### Scenario: Project entry cards stay in-shell
- **WHEN** an operator follows a workspace or board entry from a React dashboard project card
- **THEN** the shell SHALL use existing React in-shell navigation to `/app/projects/{id}` or `/app/projects/{id}/board`

#### Scenario: Dashboard routes actions to authoritative workflows
- **WHEN** an operator follows a dashboard next action, session, alarm, or full-board link
- **THEN** the browser SHALL use the existing authoritative Portal route for that workflow
- **AND** the dashboard SHALL NOT implement launch, queue, review, archive, dismiss, or other workflow mutations

#### Scenario: Empty dashboard sections explain the state
- **WHEN** no active sessions, open alarms, connected projects, or sufficient completed tasks exist
- **THEN** the dashboard SHALL render the corresponding concise empty or unavailable state
- **AND** it SHALL preserve an existing relevant workflow link where one exists

### Requirement: React dashboard JSON is authenticated and bounded
The system SHALL expose an authenticated read-only dashboard JSON handoff for the React dashboard. It SHALL derive its values from the same backend dashboard calculations as the Jinja dashboard and SHALL project only operator-facing dashboard fields.

#### Scenario: Dashboard JSON requires portal auth
- **WHEN** an unauthenticated request calls the React dashboard JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary

#### Scenario: Dashboard JSON agrees with Jinja dashboard state
- **WHEN** an authenticated operator requests the React dashboard JSON and Jinja `/dashboard` for the same database state
- **THEN** both surfaces SHALL use the same budget window, governed and Worker token totals, open-alarm state, active-session state, next-action decisions, and estimation-accuracy state

#### Scenario: Dashboard JSON does not expose raw internal records
- **WHEN** an authenticated operator requests React dashboard JSON
- **THEN** the response SHALL contain only bounded fields needed to render dashboard summaries, token details, session previews, alarm previews, accuracy, and project entry cards
- **AND** it SHALL NOT expose raw session keys, adapter configuration, secret values, or raw Worker evidence payloads

#### Scenario: Dashboard preview data is ordered and allowlisted
- **WHEN** an authenticated operator requests React dashboard JSON
- **THEN** active-session preview rows SHALL contain only `id`, task description, model, and status and SHALL include at most five newest active or running sessions first
- **AND** recent-alarm preview rows SHALL contain only `id`, type, severity, session id, and recommended action and SHALL include at most five newest unresolved alarms first
- **AND** project-entry rows SHALL contain only `id`, name, task count, and capability summary
- **AND** tests SHALL assert the nested response-key allowlists

## MODIFIED Requirements

### Requirement: React owns only the migrated project surfaces
The React Portal shell SHALL own its dashboard home, selected project workspace, and project board shell while existing Jinja pages remain available for non-migrated workflows and as dashboard fallback.

#### Scenario: Unknown React paths are not claimed
- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{project_id}`, or `/app/projects/{project_id}/board`
- **THEN** the system SHALL return not found instead of silently rendering a React surface

#### Scenario: Dashboard opens in React shell
- **WHEN** an authenticated operator explicitly opens `/app`
- **THEN** the React shell SHALL show dashboard-equivalent operator state using data supplied by FastAPI
- **AND** the existing Jinja `/dashboard` route SHALL remain reachable as a fallback

#### Scenario: Project workspace opens in React shell
- **WHEN** an authenticated operator opens the migrated project workspace route for an existing connected project
- **THEN** the React shell SHALL show project identity, readiness summary, board entry, and actionable project state using data supplied by FastAPI

#### Scenario: Project board opens in React shell
- **WHEN** an authenticated operator opens the migrated project board route for an existing connected project
- **THEN** the React shell SHALL show project-scoped board columns, compact task cards, and queue/run status
- **AND** non-migrated task intake, launch, and review workflows SHALL remain reachable through an ordinary full-page link to the Jinja project board

#### Scenario: Non-migrated pages remain available
- **WHEN** an authenticated operator opens setup, settings, sessions, alarms, login, or another non-migrated Portal page
- **THEN** the existing FastAPI/Jinja page SHALL remain reachable unless that page is explicitly migrated by a later change

### Requirement: React uses authenticated JSON handoff endpoints
The React Portal shell SHALL load dashboard, project workspace, and project board state through authenticated FastAPI JSON endpoints that reuse existing view helpers and domain logic.

#### Scenario: React state requires portal auth
- **WHEN** an unauthenticated request calls a React dashboard, project workspace, or board JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary

#### Scenario: JSON state reuses existing Portal behavior
- **WHEN** React requests dashboard or project state
- **THEN** FastAPI SHALL derive the response from existing dashboard, project, board, Worker readiness, budget, run automation, alarm, and review evidence helpers where those helpers already exist
- **AND** it SHALL NOT duplicate launch guardrail, estimation, Worker Run, budget, alarm-resolution, or review-disposition rules in frontend code

#### Scenario: Task actions stay backend-authoritative
- **WHEN** React submits task intake, estimate, launch, refresh, queue, review, archive, dismiss, or block actions
- **THEN** the request SHALL call existing FastAPI action paths or thin JSON wrappers around those paths
- **AND** backend validation SHALL remain authoritative for project binding, launch guardrails, budget acknowledgement, native usage acknowledgement, and review disposition

### Requirement: Jinja remains the default authenticated landing
The authenticated Portal landing SHALL use the existing server-rendered Jinja surface while the React shell lacks AGILE Board functional parity. The React shell SHALL remain reachable at `/app`, `/app/projects/{id}`, and `/app/projects/{id}/board` as an experimental/migrated surface, but SHALL NOT be the default landing for root, login, or logout until a later change re-enables it after parity gates pass. A missing or partial React build SHALL never leave the Portal without a usable landing.

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

### Requirement: React shell navigates client-side between its surfaces
The React Portal shell SHALL let operators move between its dashboard home, project workspace, and project board without manual URL entry, while deep links to React-owned routes still resolve on a full page load.

#### Scenario: Selecting a project opens its workspace in-shell
- **WHEN** an operator selects a project from the React dashboard or sidebar
- **THEN** the shell SHALL open that project's workspace without the operator typing a URL

#### Scenario: Moving between workspace and board stays in-shell
- **WHEN** an operator opens the board from a project workspace and returns
- **THEN** the shell SHALL navigate between those surfaces client-side without requiring a manually entered URL

#### Scenario: Deep links still resolve
- **WHEN** an operator loads or refreshes a React-owned route such as the dashboard, project workspace, or board URL directly
- **THEN** the system SHALL serve the React shell for that route as it does today

### Requirement: React shell preserves the full Portal chrome
The React Portal shell SHALL render the same application frame as the server-rendered Jinja Portal (`base.html`): a top brand bar, a left sidebar with the connected-project list and the Setup, Governance, Planning (only when no projects connected), and Settings groups, a `+ Open local repo` action, a logout form when portal auth is required, and a footer. React-owned routes inside `/app` SHALL share that frame so `/app` reads as the same product, not a separate mini-application.

#### Scenario: React shell renders the sidebar project list from the same source as Jinja
- **WHEN** an authenticated operator opens a React-owned route under `/app` with one or more connected projects
- **THEN** the shell SHALL render a sidebar listing those projects, each with its name, a `Task board` subtitle when the project has tasks or a `No tasks` subtitle when it does not, and a `└ Task board` link under projects that have tasks
- **AND** the project data SHALL come from an authenticated FastAPI JSON endpoint that reuses the same `portal_template_context` helper that feeds the Jinja sidebar
- **AND** the shell SHALL render an empty `No projects` state and a reachable `+ Open local repo` action when no projects are connected

#### Scenario: React shell renders the sidebar navigation groups
- **WHEN** an authenticated operator opens a React-owned route under `/app`
- **THEN** the shell SHALL render the `Setup` group with a `First-run setup` link, the `Governance` group with an in-shell `Dashboard` link plus full-page `Sessions` and `Alarms` links, the `Settings` group with `Control plane model`, `Token budget`, `Projects`, and `Worker adapters` links, and a footer reading `AGILE-AI-HTB portal · operator-controlled budget governance`
- **AND** the Planning group with a `Task board` link SHALL appear only when no projects are connected, matching the Jinja sidebar contract

#### Scenario: React shell shows logout when portal auth is required
- **WHEN** an authenticated operator opens a React-owned route under `/app` while portal auth is required
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
- **AND** the shell SHALL NOT mark Setup, Sessions, Alarms, or Settings group items as active, because those routes are non-migrated full-page Jinja pages whose Jinja sidebar owns active state on full load

#### Scenario: Unknown React paths return not found
- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{id}`, or `/app/projects/{id}/board`
- **THEN** FastAPI SHALL return not found instead of serving a React surface

#### Scenario: Non-migrated Jinja pages remain reachable from the React sidebar via full-page navigation
- **WHEN** an authenticated operator follows a Setup, Sessions, Alarms, Settings, Planning, task-history, or full-board link from the React sidebar
- **THEN** the browser SHALL perform an ordinary full-page navigation to the corresponding Jinja route
- **AND** React-owned routes (`/app`, `/app/projects/{id}`, `/app/projects/{id}/board`) SHALL keep using client-side navigation so in-shell moves do not do a full reload

#### Scenario: Sidebar navigation endpoint requires portal auth
- **WHEN** an unauthenticated request calls the sidebar navigation JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary
- **AND** an authenticated request SHALL receive `portal_auth_required` and a `sidebar_projects` array whose items include `id`, `name`, and `task_count`

## REMOVED Requirements

### Requirement: React shell provides a project picker home
**Reason**: `/app` must answer the operator's dashboard question rather than remain a project-picker-only alternate home.

**Migration**: Projects remain reachable through the shared sidebar and React dashboard project entry cards, which link to the existing React workspace and board routes.