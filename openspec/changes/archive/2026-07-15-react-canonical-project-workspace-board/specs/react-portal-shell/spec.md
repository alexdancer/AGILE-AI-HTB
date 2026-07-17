## MODIFIED Requirements

### Requirement: React shell provides a dashboard home
The React Portal shell SHALL render its dashboard home at the canonical `/dashboard` URL when the complete frontend build is available, and FastAPI SHALL render the existing Jinja dashboard at the same URL when the build is missing or partial. `/app` SHALL remain a transitional alias that serves the same React dashboard until the Jinja retirement change converts it to a redirect. The dashboard SHALL present operator next actions, daily governed budget, Worker execution tokens, open/critical alarm counts, budget spend breakdown and token component details, active sessions, recent open alarms, estimation accuracy when available, and connected-project entry cards.

#### Scenario: Built canonical dashboard opens in React
- **WHEN** an authenticated operator opens `/dashboard` while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** the shell SHALL render the React dashboard inside the shared Portal chrome
- **AND** it SHALL load dashboard state from an authenticated FastAPI JSON handoff

#### Scenario: Missing or partial build keeps canonical dashboard in Jinja
- **WHEN** an authenticated operator opens `/dashboard` while the React build is missing or partial
- **THEN** FastAPI SHALL render the existing Jinja dashboard at the same canonical URL
- **AND** it SHALL NOT return a blank shell or require an alternate fallback URL

#### Scenario: Explicit React home shows dashboard data
- **WHEN** an authenticated operator opens the `/app` alias after React assets are built
- **THEN** the shell SHALL render the same React dashboard inside the shared Portal chrome
- **AND** it SHALL load dashboard state from an authenticated FastAPI JSON handoff

#### Scenario: Dashboard retains project entry
- **WHEN** the dashboard has connected projects
- **THEN** it SHALL provide entry points to each project's existing React workspace and board routes
- **AND** it SHALL provide an entry point to the canonical `/projects` list

#### Scenario: Project entry cards stay in-shell
- **WHEN** an operator follows a workspace or board entry from a React dashboard project card
- **THEN** the shell SHALL use existing React in-shell navigation to the canonical `/projects/{id}` or `/projects/{id}/board`
- **AND** it SHALL NOT target the `/app` aliases, which exist only for deep links until the Jinja retirement change

#### Scenario: Dashboard routes actions to authoritative workflows
- **WHEN** an operator follows a dashboard next action, session, alarm, or full-board link
- **THEN** the browser SHALL use the existing authoritative Portal route for that workflow
- **AND** the dashboard SHALL NOT implement launch, queue, review, archive, dismiss, or other workflow mutations

#### Scenario: Dashboard does not offer a server-rendered escape link
- **WHEN** the React dashboard cannot load its state and renders an error
- **THEN** it SHALL NOT link to the server-rendered dashboard, which is a missing-build fallback rather than an operator destination
- **AND** the error SHALL be sanitized rather than rendering raw backend detail

#### Scenario: Estimation accuracy renders only when available
- **WHEN** the backend reports estimation accuracy as unavailable because no completed task carries both an estimate and an actual
- **THEN** the React dashboard SHALL NOT render the estimation-accuracy panel
- **AND** this SHALL match what the server-rendered dashboard shows for the same state

#### Scenario: Available accuracy below the reporting threshold shows progress
- **WHEN** estimation accuracy is available but fewer than three completed tasks are tracked
- **THEN** the React dashboard SHALL render the concise progress state rather than accuracy figures
- **AND** this SHALL match what the server-rendered dashboard shows for the same state

#### Scenario: Empty dashboard sections explain the state
- **WHEN** no active sessions, open alarms, or connected projects exist
- **THEN** the dashboard SHALL render the corresponding concise empty or unavailable state
- **AND** it SHALL preserve an existing relevant workflow link where one exists

### Requirement: React owns only the migrated project surfaces
The React Portal shell SHALL own its dashboard home, the Projects list, selected project workspace, project board workflow, Sessions list, Session Report, Task Breakdown Review, Project Task History, and the Alarms inbox while existing Jinja pages remain available for non-migrated workflows and as build-aware fallback for migrated surfaces. The selected React project workspace SHALL preserve the existing project overview's identity, profile, readiness, actionable summary, archive safety, and workflow navigation. The canonical `/dashboard`, `/projects`, `/projects/{project_id}`, `/projects/{project_id}/board`, `/sessions`, `/sessions/{session_id}`, `/task-breakdowns/{breakdown_id}/review`, `/projects/{project_id}/task-history`, and `/alarms` routes SHALL select React only when the complete frontend build is available. `/app/projects/{project_id}` and `/app/projects/{project_id}/board` SHALL remain transitional aliases serving the same React surfaces until the Jinja retirement change converts them to redirects.

#### Scenario: Unknown React paths are not claimed
- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{project_id}`, or `/app/projects/{project_id}/board`
- **THEN** the system SHALL return not found instead of silently rendering a React surface
- **AND** this change SHALL NOT add `/app/sessions`, `/app/sessions/{session_id}`, `/app/task-breakdowns/{breakdown_id}/review`, `/app/projects/{project_id}/task-history`, `/app/projects`, or `/app/alarms` aliases

#### Scenario: Dashboard opens in React shell
- **WHEN** an authenticated operator opens the canonical `/dashboard` or the `/app` alias while the complete build is available
- **THEN** the React shell SHALL show dashboard-equivalent operator state using data supplied by FastAPI
- **AND** the existing Jinja dashboard SHALL remain reachable as the missing/partial-build fallback at the same canonical URL

#### Scenario: Projects list opens in React shell
- **WHEN** an authenticated operator opens the canonical `/projects` while the complete build is available
- **THEN** the React shell SHALL show the connected and archived project lists using data supplied by FastAPI
- **AND** the existing Jinja projects page SHALL remain reachable as the missing/partial-build fallback at the same canonical URL

#### Scenario: Global board shim is unchanged
- **WHEN** an authenticated operator opens `/board`
- **THEN** the system SHALL preserve its existing redirect onto the first connected project's board, or onto `/projects` when no project is connected
- **AND** this change SHALL NOT give `/board` a React view

#### Scenario: Built canonical project workspace opens in React
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an existing connected project while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the project workspace inside the shared Portal chrome

#### Scenario: Missing or partial build keeps canonical project workspace in Jinja
- **WHEN** an authenticated operator opens `/projects/{project_id}` while the React build is missing or partial
- **THEN** FastAPI SHALL render the existing Jinja project workspace at the same canonical URL
- **AND** it SHALL NOT return a blank shell or require an alternate fallback URL

#### Scenario: Built canonical project board opens in React
- **WHEN** an authenticated operator opens `/projects/{project_id}/board` for an active connected project while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the project board inside the shared Portal chrome

#### Scenario: Missing or partial build keeps canonical project board in Jinja
- **WHEN** an authenticated operator opens `/projects/{project_id}/board` while the React build is missing or partial
- **THEN** FastAPI SHALL render the existing Jinja project board at the same canonical URL
- **AND** it SHALL NOT return a blank shell or require an alternate fallback URL

#### Scenario: Unknown project is rejected before the shell is served
- **WHEN** an authenticated operator opens `/projects/{project_id}` or `/projects/{project_id}/board` for a project that does not exist
- **THEN** FastAPI SHALL return its existing not-found response regardless of build availability
- **AND** it SHALL NOT serve the React shell for an unknown project

#### Scenario: Active project workspace opens with full overview state
- **WHEN** an authenticated operator opens the canonical `/projects/{project_id}` or the `/app/projects/{project_id}` alias for an active connected project
- **THEN** React SHALL show project identity, capability/readiness and reasons, canonical task counts, actionable attention state, and repository profile fields using authenticated FastAPI data
- **AND** board-targeting actions SHALL use `/projects/{project_id}/board`
- **AND** Worker setup and Project settings SHALL remain ordinary full-page links
- **AND** task history SHALL use the canonical `/projects/{project_id}/task-history` link
- **AND** Sessions SHALL use the canonical `/sessions` link

#### Scenario: Archived project workspace is restore-first
- **WHEN** an authenticated operator opens the canonical `/projects/{project_id}` or the `/app/projects/{project_id}` alias for an archived connected project
- **THEN** React SHALL show an archived warning, Restore action, and retained task-history/session evidence links
- **AND** React SHALL suppress active board and launch entry points until refreshed backend state reports the project restored

#### Scenario: Project board completes normal workflow in React shell
- **WHEN** an authenticated operator opens the migrated project board route for an active connected project
- **THEN** the React shell SHALL show project-scoped board columns, compact task cards, queue/run status, task intake, launch, refresh, review, archive/dismiss, and bounded task evidence controls using authenticated FastAPI data and actions
- **AND** backend validation SHALL remain authoritative for every workflow decision

#### Scenario: Archived React board routes to Restore
- **WHEN** an authenticated operator opens the canonical `/projects/{project_id}/board` or the `/app/projects/{project_id}/board` alias for an archived project while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell rather than redirecting to the workspace
- **AND** React SHALL clearly identify the archived state and provide a route to `/projects/{project_id}` for Restore
- **AND** the surface SHALL not present launch controls or encourage navigation to an active Jinja board

#### Scenario: Missing or partial build preserves the archived board redirect
- **WHEN** an authenticated operator opens `/projects/{project_id}/board` for an archived project while the React build is missing or partial
- **THEN** FastAPI SHALL preserve its existing redirect to the canonical project workspace carrying the existing restore-first message
- **AND** the Jinja workspace SHALL render that message at the same canonical URL

#### Scenario: Built canonical Sessions list opens in React
- **WHEN** an authenticated operator opens `/sessions` while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the Sessions list inside the shared Portal chrome

#### Scenario: Built canonical Session Report opens in React
- **WHEN** an authenticated operator opens `/sessions/{session_id}` for an existing session while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the Session Report without requiring the Jinja report for audit inspection

#### Scenario: Built canonical Task Breakdown Review opens in React
- **WHEN** an authenticated operator opens `/task-breakdowns/{breakdown_id}/review` for an existing review while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the complete review/edit/recovery workflow inside the shared Portal chrome

#### Scenario: Built canonical Project Task History opens in React
- **WHEN** an authenticated operator opens `/projects/{project_id}/task-history` for an existing project while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the Project Task History inside the shared Portal chrome without requiring the Jinja history page for archive inspection or restore

#### Scenario: Built canonical Alarms inbox opens in React
- **WHEN** an authenticated operator opens `/alarms` while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the Alarms inbox inside the shared Portal chrome without requiring the Jinja alarms page

#### Scenario: Jinja surfaces remain reachable as fallback
- **WHEN** an operator needs a missing/partial-build fallback for a migrated surface or opens setup, settings, alarms, login, or another non-migrated Portal workflow
- **THEN** the corresponding existing FastAPI/Jinja page SHALL remain reachable
- **AND** the React board SHALL not require the Jinja board to complete its normal in-board workflow

#### Scenario: Migrated project surfaces do not offer server-rendered escape links
- **WHEN** the React project workspace, project board, or Project Task History cannot load its state and renders an error
- **THEN** it SHALL NOT link to the server-rendered equivalent, which is a missing-build fallback rather than an operator destination
- **AND** the error SHALL be sanitized rather than rendering raw backend detail

### Requirement: React uses authenticated JSON handoff endpoints
The React Portal shell SHALL load dashboard, project workspace, project board, Sessions list, Session Report, Task Breakdown Review, and Alarms inbox state through authenticated FastAPI JSON endpoints that reuse existing view helpers and domain logic. The workspace endpoint SHALL return the exact bounded contract defined below, and existing Restore, board, and breakdown-review actions SHALL provide explicit JSON outcomes only to callers that negotiate `application/json` while preserving HTML redirects. Session, Task Breakdown, and Alarms handoffs SHALL be bounded, redacted, and paged where collections can grow.

#### Scenario: React state requires portal auth
- **WHEN** an unauthenticated request calls a React dashboard, project workspace, board, Sessions, Session Report, report evidence-page, full-text continuation, report-freshness, Task Breakdown Review, breakdown evidence-page, or breakdown full-text endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary

#### Scenario: JSON state reuses existing Portal behavior
- **WHEN** React requests dashboard, project, Sessions, Session Report, or Task Breakdown Review state
- **THEN** FastAPI SHALL derive the response from existing dashboard, project, board, session artifact, evidence-summary, token-accounting, related Agent Review, Task Breakdown record, candidate normalization, Worker readiness, budget, run automation, alarm, checkpoint, and review evidence helpers where those helpers already exist
- **AND** it SHALL NOT duplicate launch guardrail, estimation, Worker Run, token-accounting, Task Breakdown acceptance, Task creation, budget, alarm-resolution, archive/restore, or review-disposition rules in frontend code

#### Scenario: Workspace JSON uses exact top-level and nested keys
- **WHEN** an authenticated operator requests `/api/projects/{project_id}/workspace`
- **THEN** the response SHALL contain exactly top-level `project`, `summary`, `controls`, and `links`
- **AND** `project` SHALL contain exactly `id`, `name`, `root_path`, `archived_at`, `capability`, and `profile`
- **AND** `capability` SHALL contain exactly `state`, `label`, and `reasons`
- **AND** `profile` SHALL contain exactly `git_branch`, `language_hints`, `framework_hints`, `package_manager_hints`, `test_command`, `run_command`, and `relevant_docs`
- **AND** `summary` SHALL contain exactly `counts`, `total_tasks`, `launch_ready`, `capability_state`, and `attention_actions`
- **AND** `counts` SHALL contain exactly the canonical `Estimated`, `Running`, `Review`, `Done`, and `Blocked` non-negative integer fields
- **AND** each attention action SHALL contain exactly `label`, `detail`, `href`, and `tone`
- **AND** `controls` SHALL contain exactly `can_open_board` and `can_restore`
- **AND** `links` SHALL contain exactly `board_href`, `task_history_href`, `sessions_href`, `worker_setup_href`, `project_settings_href`, and `restore_href`

#### Scenario: Workspace JSON applies fixed bounds and safe defaults
- **WHEN** project/profile/capability/helper data contains long, missing, or malformed values
- **THEN** strings SHALL be sanitized/redacted before truncation using the design bounds
- **AND** capability reasons, profile hints/docs, and attention actions SHALL use the design item-count and per-item bounds
- **AND** wrong nested types SHALL become typed `null`, empty-list, empty-string, `false`, or zero defaults instead of producing a server error
- **AND** raw project metadata, backend ids/configuration, adapter state, secrets, session credentials, command plans, token-ledger entries, and unknown extra keys SHALL NOT be serialized

#### Scenario: Workspace links follow fixed route ownership
- **WHEN** FastAPI projects workspace links and attention actions
- **THEN** active `board_href` and board-targeting attention hrefs SHALL be exactly `/projects/{project_id}/board`
- **AND** task history, Sessions, Worker setup, and Project settings hrefs SHALL use their existing canonical routes
- **AND** unknown helper hrefs SHALL be dropped
- **AND** archived projects SHALL return `can_open_board: false`, `board_href: null`, `can_restore: true`, and `restore_href: /projects/{project_id}/restore`

#### Scenario: React Restore receives fixed success outcome
- **WHEN** React posts to `/projects/{project_id}/restore` with `Accept: application/json` for an archived or already-active project
- **THEN** the response SHALL be `200` JSON with exactly `ok`, `error`, `next_href`, `retry_href`, and `project`
- **AND** it SHALL contain `ok: true`, `error: null`, `next_href: /projects/{project_id}`, `retry_href: null`, and project fields exactly `id` and `archived: false`
- **AND** React SHALL refetch workspace and sidebar state after success rather than optimistically changing project state

#### Scenario: React Restore receives bounded unknown-project outcome
- **WHEN** a JSON-negotiated Restore targets an unknown project
- **THEN** the response SHALL return `404` using the same fixed envelope with `ok: false`, sanitized error text bounded to 1000 characters, `next_href: null`, `project: null`, and `retry_href: /projects`
- **AND** React SHALL not refetch or infer project state from the failed outcome

#### Scenario: HTML Restore behavior remains unchanged
- **WHEN** an ordinary form caller posts Restore without explicitly negotiating `application/json`
- **THEN** the existing idempotent restore behavior SHALL remain authoritative
- **AND** the response SHALL remain a `303` redirect to `/projects/{project_id}`

#### Scenario: Task actions stay backend-authoritative
- **WHEN** React submits task intake, estimate, launch, refresh, queue, review, archive, dismiss, block, Task Breakdown Accept, Retry, or Manual Candidate actions
- **THEN** the request SHALL call existing FastAPI action paths or thin JSON wrappers around those paths
- **AND** backend validation SHALL remain authoritative for project binding, candidate normalization, Task Estimation, launch guardrails, budget acknowledgement, native usage acknowledgement, and review disposition

### Requirement: React is the build-aware default authenticated landing
The normal Portal landing SHALL use the React dashboard at the canonical `/dashboard` when the complete built React shell is available. The system SHALL validate the React index and all referenced local React assets before choosing `/dashboard`; when that validation fails, the normal landing SHALL remain the existing server-rendered first-project or `/projects` route. This promotion SHALL NOT remove explicit Jinja fallback routes. React route ownership SHALL include `/dashboard`, `/projects`, `/projects/{id}`, `/projects/{id}/board`, `/app`, `/app/projects/{id}`, `/app/projects/{id}/board`, `/sessions`, `/sessions/{session_id}`, `/task-breakdowns/{breakdown_id}/review`, `/setup`, and the destination Settings routes `/settings/control-plane`, `/settings/budget`, `/settings/project`, and `/settings/workers` only for the migrated surfaces defined by this specification.

#### Scenario: Auth-disabled local root opens built React dashboard
- **WHEN** portal auth is not required and an operator opens `/` while the complete React build is available
- **THEN** the system SHALL redirect to `/dashboard`
- **AND** the React shell SHALL render its dashboard inside the full Portal chrome

#### Scenario: Successful login opens built React dashboard
- **WHEN** portal auth is required and an operator submits a valid portal token while the complete React build is available
- **THEN** the system SHALL preserve the existing signed cookie behavior
- **AND** the successful login response SHALL redirect to `/dashboard`

#### Scenario: Authenticated root opens built React dashboard
- **WHEN** portal auth is required and an authenticated operator opens `/` while the complete React build is available
- **THEN** the system SHALL redirect to `/dashboard`

#### Scenario: Unauthenticated shared root still requires login
- **WHEN** portal auth is required and an unauthenticated operator opens `/`
- **THEN** the system SHALL redirect to `/login`
- **AND** build availability SHALL NOT bypass the existing authentication boundary

#### Scenario: Auth-disabled login and logout use normal landing
- **WHEN** portal auth is not required and an operator opens `/login`, submits a well-formed `/login` request containing the existing required token form field, or submits `/logout`
- **THEN** the system SHALL preserve existing harmless login/logout behavior
- **AND** it SHALL redirect to `/dashboard` when the complete React build is available

#### Scenario: Missing React index falls back to Jinja landing
- **WHEN** a normal landing decision occurs and the React index is missing
- **THEN** the system SHALL redirect to the existing server-rendered first-project route when a connected project exists, otherwise `/projects`
- **AND** the operator SHALL NOT receive a blank shell or missing-build `503` as the default landing

#### Scenario: Partial React build falls back to Jinja landing
- **WHEN** the React index exists but one or more referenced local React assets are missing or invalid
- **THEN** the normal landing SHALL use the existing server-rendered first-project or `/projects` route
- **AND** the system SHALL NOT promote the partial shell

#### Scenario: Fallback landing on the canonical Projects route serves Jinja
- **WHEN** the normal landing falls back to `/projects` because the React build is missing or partial
- **THEN** that canonical route SHALL render the existing Jinja projects page for the same build state
- **AND** the operator SHALL NOT be redirected into a shell that cannot load

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

- **WHEN** an authenticated operator opens a project workspace or project board at the canonical `/projects/{id}` or `/projects/{id}/board`, or at the `/app/projects/{id}` or `/app/projects/{id}/board` alias
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

#### Scenario: Non-migrated Jinja pages remain reachable from the React sidebar via full-page navigation

- **WHEN** an authenticated operator follows an Alarms, Settings, Planning, task-history, or full-board link from the React sidebar
- **THEN** the browser SHALL perform an ordinary full-page navigation to the corresponding canonical route rather than an in-shell transition
- **AND** the shell's own in-shell surfaces SHALL use client-side navigation so in-shell moves do not require a full reload

#### Scenario: Sidebar navigation endpoint requires portal auth

- **WHEN** an unauthenticated request calls the sidebar navigation JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary
- **AND** an authenticated request SHALL receive `portal_auth_required` and a `sidebar_projects` array whose items include `id`, `name`, and `task_count`

