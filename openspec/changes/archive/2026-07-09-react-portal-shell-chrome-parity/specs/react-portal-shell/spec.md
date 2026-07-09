## ADDED Requirements

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