## ADDED Requirements

### Requirement: React Projects list JSON is authenticated, exact, and bounded
The existing authenticated projects JSON handoff SHALL additionally project the archived connected projects and the Local Runner enablement flag, so the frontend can render the canonical Projects list without recomputing project rules in the browser. Both values SHALL derive from the same backend listings and settings flag the server-rendered projects page uses. The existing active-projects projection SHALL be unchanged so current consumers are unaffected.

#### Scenario: Projects JSON requires portal auth
- **WHEN** an unauthenticated caller requests the projects JSON handoff while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary
- **AND** it SHALL NOT return project data, including connected project root paths

#### Scenario: Projects JSON carries archived projects and Local Runner state
- **WHEN** an authenticated operator requests the projects JSON handoff
- **THEN** the response SHALL include the existing active `projects` array unchanged, an `archived_projects` array, and `local_runner_enabled`
- **AND** each archived row SHALL contain only `id`, name, root path, sanitized capability state, and the archive timestamp
- **AND** absent optional values SHALL be typed `null` rather than fabricated defaults

#### Scenario: Projects JSON agrees with the server-rendered projects page
- **WHEN** an authenticated operator requests the projects JSON handoff and the Jinja `/projects` page for the same database state
- **THEN** both surfaces SHALL show the same active projects, archived projects, capability states, and Local Runner enablement
- **AND** both SHALL derive those values from the same backend project listings rather than a parallel computation

#### Scenario: Projects JSON does not expose raw internal records
- **WHEN** an authenticated operator requests the projects JSON handoff
- **THEN** capability reasons SHALL be bounded by the existing evidence-safety helper
- **AND** the response SHALL NOT expose adapter configuration, secret values, raw exception text, or raw Worker evidence payloads

#### Scenario: Existing consumers are unaffected
- **WHEN** the React board, project workspace, or Project Task History requests the projects JSON handoff
- **THEN** the existing `projects` array SHALL retain its current fields, ordering, and task counts
- **AND** the added fields SHALL NOT change those consumers' behavior

### Requirement: React Projects list navigates inside the shell
React SHALL render the Projects list inside the shared Portal chrome on the canonical `/projects` URL when the complete build is available, and FastAPI SHALL render the existing Jinja projects page at the same URL when the build is missing or partial. The view SHALL preserve the open-local-repo form, the Local-Runner-disabled notice, per-project capability, project entry cards, Archive, and the archived list with Restore.

#### Scenario: Built canonical route opens React Projects in-shell
- **WHEN** an authenticated operator opens `/projects` while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell and render the Projects list inside the full Portal chrome
- **AND** React SHALL request the authenticated projects JSON for its active projects, archived projects, capability, and Local Runner state

#### Scenario: Missing or partial build keeps canonical Projects in Jinja
- **WHEN** an authenticated operator opens `/projects` while the React build is missing or partial
- **THEN** FastAPI SHALL render the existing Jinja projects page at the same canonical URL
- **AND** it SHALL NOT return a blank shell or require an alternate fallback URL

#### Scenario: Project entry cards open the React workspace
- **WHEN** an authenticated operator selects an active project from the React Projects list
- **THEN** the shell SHALL open that project's React workspace without a full-page transition to a server-rendered workspace
- **AND** the card SHALL show the project's sanitized capability state

#### Scenario: Local Runner disabled is stated before connecting
- **WHEN** an operator opens the React Projects list while the Local Runner is disabled
- **THEN** React SHALL show the existing disabled notice and its enablement guidance
- **AND** the open-local-repo form SHALL remain visible rather than being silently removed

#### Scenario: Connect, archive, and restore stay on page with inline outcome
- **WHEN** an operator opens a local repo, archives an active project, or restores an archived project from the React Projects list and the action succeeds
- **THEN** React SHALL consume the existing negotiated JSON outcome of that action without altering its shape
- **AND** React SHALL refetch authoritative projects state rather than optimistically trusting the submitted values

#### Scenario: Blocked archive is sanitized on the Projects list
- **WHEN** an operator archives a project from the React Projects list and the backend blocks it
- **THEN** React SHALL surface the backend's sanitized block reason
- **AND** raw backend exception detail SHALL NOT reach the operator

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
- **THEN** the shell SHALL use existing React in-shell navigation to `/app/projects/{id}` or `/app/projects/{id}/board`

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
The React Portal shell SHALL own its dashboard home, the Projects list, selected project workspace, project board workflow, Sessions list, Session Report, Task Breakdown Review, Project Task History, and the Alarms inbox while existing Jinja pages remain available for non-migrated workflows and as build-aware fallback for migrated surfaces. The selected React project workspace SHALL preserve the existing project overview's identity, profile, readiness, actionable summary, archive safety, and workflow navigation. The canonical `/dashboard`, `/projects`, `/sessions`, `/sessions/{session_id}`, `/task-breakdowns/{breakdown_id}/review`, `/projects/{project_id}/task-history`, and `/alarms` routes SHALL select React only when the complete frontend build is available. The canonical `/projects/{project_id}` and `/projects/{project_id}/board` routes SHALL continue to render Jinja until a following change migrates them.

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

#### Scenario: Active project workspace opens with full overview state
- **WHEN** an authenticated operator opens `/app/projects/{project_id}` for an active connected project
- **THEN** React SHALL show project identity, capability/readiness and reasons, canonical task counts, actionable attention state, and repository profile fields using authenticated FastAPI data
- **AND** board-targeting actions SHALL use `/app/projects/{project_id}/board`
- **AND** Worker setup and Project settings SHALL remain ordinary full-page links
- **AND** task history SHALL use the canonical `/projects/{project_id}/task-history` link
- **AND** Sessions SHALL use the canonical `/sessions` link

#### Scenario: Archived project workspace is restore-first
- **WHEN** an authenticated operator opens `/app/projects/{project_id}` for an archived connected project
- **THEN** React SHALL show an archived warning, Restore action, and retained task-history/session evidence links
- **AND** React SHALL suppress active board and launch entry points until refreshed backend state reports the project restored

#### Scenario: Project board completes normal workflow in React shell
- **WHEN** an authenticated operator opens the migrated project board route for an active connected project
- **THEN** the React shell SHALL show project-scoped board columns, compact task cards, queue/run status, task intake, launch, refresh, review, archive/dismiss, and bounded task evidence controls using authenticated FastAPI data and actions
- **AND** backend validation SHALL remain authoritative for every workflow decision

#### Scenario: Archived React board routes to Restore
- **WHEN** an authenticated operator opens `/app/projects/{project_id}/board` for an archived project
- **THEN** React SHALL clearly identify the archived state and provide a route to `/app/projects/{project_id}` for Restore
- **AND** the surface SHALL not present launch controls or encourage navigation to an active Jinja board

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

### Requirement: React is the build-aware default authenticated landing
The normal Portal landing SHALL use the React dashboard at the canonical `/dashboard` when the complete built React shell is available. The system SHALL validate the React index and all referenced local React assets before choosing `/dashboard`; when that validation fails, the normal landing SHALL remain the existing server-rendered first-project or `/projects` route. This promotion SHALL NOT remove explicit Jinja fallback routes. React route ownership SHALL include `/dashboard`, `/projects`, `/app`, `/app/projects/{id}`, `/app/projects/{id}/board`, `/sessions`, `/sessions/{session_id}`, `/task-breakdowns/{breakdown_id}/review`, `/setup`, and the destination Settings routes `/settings/control-plane`, `/settings/budget`, `/settings/project`, and `/settings/workers` only for the migrated surfaces defined by this specification.

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

### Requirement: React shell navigates client-side between its surfaces
The React Portal shell SHALL let operators move between its dashboard home, Projects list, project workspace, project board, Sessions, Session Report, and Task Breakdown Review without manual URL entry, while deep links to React-owned routes still resolve on a full page load.

#### Scenario: Selecting a project opens its workspace in-shell
- **WHEN** an operator selects a project from the React dashboard, the React Projects list, or the sidebar
- **THEN** the shell SHALL open that project's workspace without the operator typing a URL

#### Scenario: Moving between the Projects list and the dashboard stays in-shell
- **WHEN** an operator moves between the canonical `/dashboard` and `/projects` routes using shell navigation
- **THEN** the shell SHALL navigate client-side without a full-page transition
- **AND** browser Back and Forward SHALL preserve those route transitions

#### Scenario: Moving between workspace and board stays in-shell
- **WHEN** an operator opens the board from a project workspace and returns
- **THEN** the shell SHALL navigate between those surfaces client-side without requiring a manually entered URL

#### Scenario: Board intake opens Task Breakdown Review in-shell
- **WHEN** a React board intake outcome provides `/task-breakdowns/{breakdown_id}/review`
- **THEN** the shell SHALL navigate to that canonical review route without a full-page Jinja transition
- **AND** browser Back/Forward SHALL preserve the route transition subject to the review's unsaved-draft guard

#### Scenario: Review Session and board links preserve route ownership
- **WHEN** an operator follows the review's Session Report or canonical React project board link
- **THEN** the shell SHALL use client-side navigation for the React-owned target
- **AND** global or still-non-migrated targets SHALL use their authoritative route behavior

#### Scenario: Deep links still resolve
- **WHEN** an operator loads or refreshes a React-owned route such as the canonical dashboard, Projects list, project workspace, board, Sessions, Session Report, or Task Breakdown Review URL directly
- **THEN** the system SHALL serve the React shell for that existing resource route when the complete build is available
