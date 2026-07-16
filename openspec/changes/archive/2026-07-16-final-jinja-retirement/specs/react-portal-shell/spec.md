## MODIFIED Requirements

### Requirement: FastAPI serves the React Portal shell
The system SHALL serve a built Vite React Portal shell from the existing FastAPI application without introducing a separate Node runtime server.

#### Scenario: Built React shell is available
- **WHEN** an authenticated operator opens a route owned by the React Portal shell after frontend assets have been built
- **THEN** FastAPI SHALL return the React shell `index.html`
- **AND** React asset files SHALL be served from the same FastAPI process

#### Scenario: React assets are missing
- **WHEN** an authenticated operator opens a React-owned route and the built frontend assets are not available
- **THEN** the system SHALL return the missing-build recovery response
- **AND** the response SHALL NOT silently render a broken blank shell
- **AND** no server-rendered equivalent of that surface SHALL exist to fall back to

#### Scenario: No separate frontend server is required in production
- **WHEN** Foreman AI HQ is served for normal operator use after the React frontend is built
- **THEN** the operator SHALL NOT need to run `vite`, `npm run dev`, or another Node server to use the migrated Portal surface

### Requirement: React shell provides a dashboard home
The React Portal shell SHALL render its dashboard home at the canonical `/dashboard` URL when the complete frontend build is available, and that URL SHALL return the missing-build recovery response when the build is missing or partial. `/app` SHALL permanently redirect to `/dashboard`. The dashboard SHALL present operator next actions, daily governed budget, Worker execution tokens, open/critical alarm counts, budget spend breakdown and token component details, active sessions, recent open alarms, estimation accuracy when available, and connected-project entry cards.

#### Scenario: Built canonical dashboard opens in React
- **WHEN** an authenticated operator opens `/dashboard` while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** the shell SHALL render the React dashboard inside the shared Portal chrome
- **AND** it SHALL load dashboard state from an authenticated FastAPI JSON handoff

#### Scenario: Missing or partial build returns the recovery response at the canonical dashboard
- **WHEN** an authenticated operator opens `/dashboard` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** it SHALL NOT return a blank shell or redirect to an alternate URL

#### Scenario: Explicit `/app` deep link redirects to the canonical dashboard
- **WHEN** an authenticated operator opens the `/app` alias
- **THEN** FastAPI SHALL issue a permanent redirect to `/dashboard`
- **AND** the canonical route SHALL then decide between the React dashboard and the recovery response according to build availability

#### Scenario: Dashboard retains project entry
- **WHEN** the dashboard has connected projects
- **THEN** it SHALL provide entry points to each project's existing React workspace and board routes
- **AND** it SHALL provide an entry point to the canonical `/projects` list

#### Scenario: Project entry cards stay in-shell
- **WHEN** an operator follows a workspace or board entry from a React dashboard project card
- **THEN** the shell SHALL use existing React in-shell navigation to the canonical `/projects/{id}` or `/projects/{id}/board`
- **AND** it SHALL NOT target the `/app` aliases, which are permanent redirects retained only for existing bookmarks and external links

#### Scenario: Dashboard routes actions to authoritative workflows
- **WHEN** an operator follows a dashboard next action, session, alarm, or full-board link
- **THEN** the browser SHALL use the existing authoritative Portal route for that workflow
- **AND** the dashboard SHALL NOT implement launch, queue, review, archive, dismiss, or other workflow mutations

#### Scenario: Dashboard does not offer a server-rendered escape link
- **WHEN** the React dashboard cannot load its state and renders an error
- **THEN** it SHALL render a sanitized error rather than raw backend detail
- **AND** it SHALL NOT link to a server-rendered dashboard equivalent, which no longer exists

#### Scenario: Estimation accuracy renders only when available
- **WHEN** the backend reports estimation accuracy as unavailable because no completed task carries both an estimate and an actual
- **THEN** the React dashboard SHALL NOT render the estimation-accuracy panel

#### Scenario: Available accuracy below the reporting threshold shows progress
- **WHEN** estimation accuracy is available but fewer than three completed tasks are tracked
- **THEN** the React dashboard SHALL render the concise progress state rather than accuracy figures

#### Scenario: Empty dashboard sections explain the state
- **WHEN** no active sessions, open alarms, or connected projects exist
- **THEN** the dashboard SHALL render the corresponding concise empty or unavailable state
- **AND** it SHALL preserve an existing relevant workflow link where one exists

### Requirement: React dashboard JSON is authenticated and bounded
The system SHALL expose an authenticated read-only dashboard JSON handoff for the React dashboard. It SHALL derive its values from the existing backend dashboard calculation rather than a parallel computation, and SHALL project only operator-facing dashboard fields.

#### Scenario: Dashboard JSON requires portal auth
- **WHEN** an unauthenticated request calls the React dashboard JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary

#### Scenario: Dashboard JSON derives from the single backend dashboard calculation
- **WHEN** an authenticated operator requests the React dashboard JSON
- **THEN** the budget window, governed and Worker token totals, open-alarm state, active-session state, next-action decisions, and estimation-accuracy state SHALL be read from the existing shared dashboard context builder
- **AND** the endpoint SHALL NOT recompute any of those values independently of that builder

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

### Requirement: React owns only the migrated project surfaces
The React Portal shell SHALL own its dashboard home, the Projects list, selected project workspace, project board workflow, Sessions list, Session Report, Task Breakdown Review, Project Task History, and the Alarms inbox. No server-rendered equivalent of those surfaces SHALL remain. The selected React project workspace SHALL preserve the existing project overview's identity, profile, readiness, actionable summary, archive safety, and workflow navigation. The canonical `/dashboard`, `/projects`, `/projects/{project_id}`, `/projects/{project_id}/board`, `/sessions`, `/sessions/{session_id}`, `/task-breakdowns/{breakdown_id}/review`, `/projects/{project_id}/task-history`, and `/alarms` routes SHALL serve React when the complete frontend build is available and SHALL return the missing-build recovery response otherwise. `/app/projects/{project_id}` and `/app/projects/{project_id}/board` SHALL permanently redirect to their canonical URLs.

#### Scenario: Unknown React paths are not claimed
- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{project_id}`, or `/app/projects/{project_id}/board`
- **THEN** the system SHALL return not found instead of silently redirecting or rendering a React surface

#### Scenario: Dashboard opens in React shell
- **WHEN** an authenticated operator opens the canonical `/dashboard` while the complete build is available
- **THEN** the React shell SHALL show dashboard-equivalent operator state using data supplied by FastAPI

#### Scenario: Projects list opens in React shell
- **WHEN** an authenticated operator opens the canonical `/projects` while the complete build is available
- **THEN** the React shell SHALL show the connected and archived project lists using data supplied by FastAPI

#### Scenario: Global board shim is unchanged
- **WHEN** an authenticated operator opens `/board`
- **THEN** the system SHALL preserve its existing redirect onto the first connected project's board, or onto `/projects` when no project is connected
- **AND** this change SHALL NOT give `/board` a React view

#### Scenario: Built canonical project workspace opens in React
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an existing connected project while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the project workspace inside the shared Portal chrome

#### Scenario: Missing or partial build returns the recovery response at the canonical project workspace
- **WHEN** an authenticated operator opens `/projects/{project_id}` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** it SHALL NOT return a blank shell or redirect to an alternate URL

#### Scenario: Built canonical project board opens in React
- **WHEN** an authenticated operator opens `/projects/{project_id}/board` for an active connected project while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the project board inside the shared Portal chrome

#### Scenario: Missing or partial build returns the recovery response at the canonical project board
- **WHEN** an authenticated operator opens `/projects/{project_id}/board` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** it SHALL NOT return a blank shell or redirect to an alternate URL

#### Scenario: Unknown project is rejected before the shell is served
- **WHEN** an authenticated operator opens `/projects/{project_id}` or `/projects/{project_id}/board` for a project that does not exist
- **THEN** FastAPI SHALL return its existing not-found response regardless of build availability
- **AND** it SHALL NOT serve the React shell or the recovery response for an unknown project

#### Scenario: Active project workspace opens with full overview state
- **WHEN** an authenticated operator opens the canonical `/projects/{project_id}` for an active connected project
- **THEN** React SHALL show project identity, capability/readiness and reasons, canonical task counts, actionable attention state, and repository profile fields using authenticated FastAPI data
- **AND** board-targeting actions SHALL use `/projects/{project_id}/board`
- **AND** Worker setup and Project settings SHALL remain ordinary full-page links
- **AND** task history SHALL use the canonical `/projects/{project_id}/task-history` link
- **AND** Sessions SHALL use the canonical `/sessions` link

#### Scenario: Archived project workspace is restore-first
- **WHEN** an authenticated operator opens the canonical `/projects/{project_id}` for an archived connected project
- **THEN** React SHALL show an archived warning, Restore action, and retained task-history/session evidence links
- **AND** React SHALL suppress active board and launch entry points until refreshed backend state reports the project restored

#### Scenario: Project board completes normal workflow in React shell
- **WHEN** an authenticated operator opens the canonical project board route for an active connected project
- **THEN** the React shell SHALL show project-scoped board columns, compact task cards, queue/run status, task intake, launch, refresh, review, archive/dismiss, and bounded task evidence controls using authenticated FastAPI data and actions
- **AND** backend validation SHALL remain authoritative for every workflow decision

#### Scenario: Archived React board routes to Restore
- **WHEN** an authenticated operator opens the canonical `/projects/{project_id}/board` for an archived project while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell rather than redirecting to the workspace
- **AND** React SHALL clearly identify the archived state and provide a route to `/projects/{project_id}` for Restore
- **AND** the surface SHALL not present launch controls

#### Scenario: Missing or partial build returns the recovery response for an archived board
- **WHEN** an authenticated operator opens `/projects/{project_id}/board` for an archived project while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response
- **AND** the restore-first message SHALL NOT require a server-rendered workspace to carry it

#### Scenario: Built canonical Sessions list opens in React
- **WHEN** an authenticated operator opens `/sessions` while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the Sessions list inside the shared Portal chrome

#### Scenario: Built canonical Session Report opens in React
- **WHEN** an authenticated operator opens `/sessions/{session_id}` for an existing session while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the Session Report as the only audit-inspection surface

#### Scenario: Missing or partial build returns the recovery response at canonical Sessions
- **WHEN** an authenticated operator opens `/sessions` or `/sessions/{session_id}` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** session evidence SHALL be unavailable until the frontend is built, rather than diverting to a server-rendered sessions list or report

#### Scenario: Built canonical Task Breakdown Review opens in React
- **WHEN** an authenticated operator opens `/task-breakdowns/{breakdown_id}/review` for an existing review while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the complete review/edit/recovery workflow inside the shared Portal chrome

#### Scenario: Built canonical Project Task History opens in React
- **WHEN** an authenticated operator opens `/projects/{project_id}/task-history` for an existing project while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the Project Task History as the only archive-inspection and restore surface

#### Scenario: Built canonical Alarms inbox opens in React
- **WHEN** an authenticated operator opens `/alarms` while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the Alarms inbox inside the shared Portal chrome

#### Scenario: Missing or partial build returns the recovery response at the canonical Alarms inbox
- **WHEN** an authenticated operator opens `/alarms` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** governance evidence SHALL remain in the database rather than being diverted to a server-rendered alarms page

#### Scenario: Only the recovery surfaces remain server-rendered
- **WHEN** the Jinja retirement change is implemented
- **THEN** the only server-rendered Portal pages SHALL be the login page and the missing-build recovery response
- **AND** no operator-facing route SHALL render a retired template

#### Scenario: Migrated project surfaces do not offer server-rendered escape links
- **WHEN** the React project workspace, project board, or Project Task History cannot load its state and renders an error
- **THEN** it SHALL render a sanitized error rather than raw backend detail
- **AND** it SHALL NOT link to a server-rendered equivalent, which no longer exists

### Requirement: React shell preserves the full Portal chrome

The React Portal shell SHALL render the full Portal application frame: a top brand bar, a left sidebar with the connected-project list and the Setup, Governance, Planning (only when no projects connected), and Settings groups, a `+ Open local repo` action, a logout form when portal auth is required, and a footer. React-owned routes SHALL share that frame so every canonical Portal route reads as the same product. React SHALL be the sole owner of this frame; no server-rendered template SHALL define it.

#### Scenario: React shell renders the sidebar project list from the shared context helper

- **WHEN** an authenticated operator opens a React-owned route with one or more connected projects
- **THEN** the shell SHALL render a sidebar listing those projects, each with its name, a `Task board` subtitle when the project has tasks or a `No tasks` subtitle when it does not, and a `└ Task board` link under projects that have tasks
- **AND** the project data SHALL come from an authenticated FastAPI JSON endpoint that reuses the existing `portal_template_context` helper
- **AND** the shell SHALL render an empty `No projects` state and a reachable `+ Open local repo` action when no projects are connected

#### Scenario: React shell renders the sidebar navigation groups

- **WHEN** an authenticated operator opens a React-owned route
- **THEN** the shell SHALL render the `Setup` group with a `First-run setup` link, the `Governance` group with an in-shell `Dashboard` link plus `Sessions` and full-page `Alarms` links, the `Settings` group with `Control plane model`, `Token budget`, `Projects`, and `Worker adapters` links, and a footer reading `Foreman AI HQ portal · operator-controlled budget governance`
- **AND** the Planning group with a `Task board` link SHALL appear only when no projects are connected

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

#### Scenario: Full-page sidebar links remain full-page navigations

- **WHEN** an authenticated operator follows an Alarms, Settings, Planning, task-history, or full-board link from the React sidebar
- **THEN** the browser SHALL perform an ordinary full-page navigation to the corresponding canonical route rather than an in-shell transition
- **AND** that canonical route SHALL serve the React shell, which renders the destination surface
- **AND** the shell's own in-shell surfaces SHALL use client-side navigation so in-shell moves do not require a full reload

#### Scenario: Sidebar navigation endpoint requires portal auth

- **WHEN** an unauthenticated request calls the sidebar navigation JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary
- **AND** an authenticated request SHALL receive `portal_auth_required` and a `sidebar_projects` array whose items include `id`, `name`, and `task_count`

### Requirement: React Budget Settings navigates inside the shell
React SHALL render Budget Settings inside the shared Portal chrome on the canonical `/settings/budget` URL when the complete build is available, keep `Back to setup` as an ordinary full-page link, and require confirmation before the destructive counter reset. When the React build is missing or partial, that URL SHALL return the missing-build recovery response.

#### Scenario: Built canonical route opens React Budget Settings in-shell
- **WHEN** an authenticated operator opens `/settings/budget` while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell and render Budget Settings inside the full Portal chrome
- **AND** React SHALL request the authenticated Budget Settings JSON for its form and counter

#### Scenario: Missing or partial build returns the recovery response at canonical Budget Settings
- **WHEN** an authenticated operator opens `/settings/budget` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** it SHALL NOT return a blank shell or redirect to an alternate URL

#### Scenario: Save stays on page with inline outcome and authoritative refetch
- **WHEN** an operator saves caps from the React Budget Settings view and the save succeeds
- **THEN** React SHALL show an inline success outcome without leaving the Budget Settings page
- **AND** React SHALL refetch authoritative budget state rather than optimistically trusting the submitted values

#### Scenario: Reset requires confirmation
- **WHEN** an operator triggers the daily-counter reset from the React Budget Settings view
- **THEN** React SHALL require an explicit confirmation before submitting the reset
- **AND** it SHALL surface the outcome inline and refetch authoritative counter state

### Requirement: React Control Plane Settings navigates inside the shell
React SHALL render Control Plane Settings inside the shared Portal chrome on the canonical `/settings/control-plane` URL when the complete build is available, and that URL SHALL return the missing-build recovery response when the build is missing or partial. The view SHALL preserve provider-filtered curated model selection with a custom-model path, placeholder-only key entry, the three-state connection status, and the environment-shadow warning.

#### Scenario: Built canonical route opens React Control Plane Settings in-shell
- **WHEN** an authenticated operator opens `/settings/control-plane` while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell and render Control Plane Settings inside the full Portal chrome
- **AND** React SHALL request the authenticated control-plane JSON for its form and status

#### Scenario: Missing or partial build returns the recovery response at canonical Control Plane Settings
- **WHEN** an authenticated operator opens `/settings/control-plane` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** it SHALL NOT return a blank shell or redirect to an alternate URL

#### Scenario: Key input is placeholder-only and blank keeps the existing key
- **WHEN** the React Control Plane Settings form renders
- **THEN** the API key input SHALL be a password field that is empty by default and never prefilled with the stored key
- **AND** submitting the form with the key field blank SHALL preserve the existing stored key through the existing backend behavior

#### Scenario: Dirty form disables the connection test
- **WHEN** the operator has unsaved edits in the React Control Plane Settings form
- **THEN** React SHALL disable the Test action and show an inline hint to save before testing
- **AND** after a successful save the form SHALL become pristine and the Test action SHALL re-enable with status shown as `needs_test`

#### Scenario: Provider selection filters the curated model dropdown
- **WHEN** the operator changes the provider in the React form
- **THEN** the curated model dropdown SHALL show only that provider's curated choices and otherwise expose the custom-model path
- **AND** an existing saved model outside the curated choices SHALL be preserved through the custom-model path

#### Scenario: Save stays on page with inline outcome and authoritative refetch
- **WHEN** an operator saves control-plane settings from the React view and the save succeeds
- **THEN** React SHALL show an inline success outcome without leaving the page
- **AND** React SHALL refetch authoritative control-plane state rather than optimistically trusting the submitted values

### Requirement: React Worker Settings navigates inside the shell
React SHALL render Worker Settings inside the shared Portal chrome on the canonical `/settings/workers` URL when the complete build is available, and that URL SHALL return the missing-build recovery response when the build is missing or partial. The view SHALL preserve adapter selection, per-adapter configuration and evidence, the discover→approve model workflow, the live Verify and Discover actions, and the readiness next-action.

#### Scenario: Built canonical route opens React Worker Settings in-shell
- **WHEN** an authenticated operator opens `/settings/workers` while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell and render Worker Settings inside the full Portal chrome
- **AND** React SHALL request the authenticated Worker Settings JSON for its adapters, selection, and next-action

#### Scenario: Missing or partial build returns the recovery response at canonical Worker Settings
- **WHEN** an authenticated operator opens `/settings/workers` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** it SHALL NOT return a blank shell or redirect to an alternate URL

#### Scenario: Approval is gated behind discovery
- **WHEN** the React Worker Settings view renders an adapter that has no discovered models
- **THEN** the model-approval control SHALL offer only discovered models and SHALL be unavailable until discovery has run for that adapter
- **AND** this SHALL mirror the existing server rule that rejects approval of models not yet discovered

#### Scenario: Live action stays on page with inline outcome and authoritative refetch
- **WHEN** an operator runs Verify or Discover models from the React view
- **THEN** React SHALL show the inline pass/fail outcome and sanitized reasons without leaving the page
- **AND** React SHALL refetch authoritative Worker Settings state and keep the operator on the adapter they were editing rather than resetting to the default adapter

#### Scenario: Set-default and approval stay on page with inline outcome
- **WHEN** an operator marks an adapter as default or approves models from the React view and the action succeeds
- **THEN** React SHALL show an inline success outcome without leaving the page
- **AND** React SHALL refetch authoritative Worker Settings state rather than optimistically trusting the submitted values

### Requirement: React Project Settings navigates inside the shell
React SHALL render Project Settings inside the shared Portal chrome on the canonical `/settings/project` URL when the complete build is available, and that URL SHALL return the missing-build recovery response when the build is missing or partial. The view SHALL preserve the connect-project form, the Local Runner backend-status panel, per-project capability, the read-only-proof action, and archive/restore.

#### Scenario: Built canonical route opens React Project Settings in-shell
- **WHEN** an authenticated operator opens `/settings/project` while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell and render Project Settings inside the full Portal chrome
- **AND** React SHALL request the authenticated Project Settings JSON for its projects, backend status, and capability

#### Scenario: Missing or partial build returns the recovery response at canonical Project Settings
- **WHEN** an authenticated operator opens `/settings/project` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** it SHALL NOT return a blank shell or redirect to an alternate URL

#### Scenario: Connect and archive stay on page with inline outcome and authoritative refetch
- **WHEN** an operator connects a project or archives a connected project from the React view and the action succeeds
- **THEN** React SHALL show an inline success outcome without leaving the page
- **AND** React SHALL refetch authoritative Project Settings state rather than optimistically trusting the submitted values

#### Scenario: Read-only proof stays on page with inline outcome
- **WHEN** an operator runs the read-only launch proof from the React view
- **THEN** React SHALL show the inline pass or guardrail-block outcome without leaving the page
- **AND** React SHALL refetch authoritative Project Settings state after the proof completes

#### Scenario: Redirect-borne archive block reason survives into React
- **WHEN** an HTML archive caller is blocked and redirected to the project settings page with an error query, and the complete React build serves that canonical URL
- **THEN** React SHALL surface that block reason rather than silently dropping it
- **AND** the reason SHALL be sanitized and bounded by the backend rather than rendered from the URL directly
- **AND** React SHALL clear the redirect-borne error once the operator takes a subsequent action

### Requirement: React Setup Overview navigates inside the shell
React SHALL render Setup Overview inside the shared Portal chrome on the canonical `/setup` URL when the complete build is available, and that URL SHALL return the missing-build recovery response when the build is missing or partial. The view SHALL preserve the next-action toolbar, the four readiness cards with their destination links, the launch-readiness panel, and the active Worker adapter panel. The Setup sidebar link SHALL use in-shell client navigation.

#### Scenario: Built canonical route opens React Setup Overview in-shell
- **WHEN** an authenticated operator opens `/setup` while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell and render Setup Overview inside the full Portal chrome
- **AND** React SHALL request the authenticated Setup Overview JSON for its readiness steps, next action, and active adapter

#### Scenario: Missing or partial build returns the recovery response at canonical Setup Overview
- **WHEN** an authenticated operator opens `/setup` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** it SHALL NOT return a blank shell or redirect to an alternate URL

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

#### Scenario: Tracking is read from one source
- **WHEN** the React Setup Overview renders the tracking of the active Worker adapter
- **THEN** it SHALL read the tracking mode from the Worker adapter view model rather than from raw verification evidence
- **AND** an adapter whose tracking has not been verified SHALL render as unverified

### Requirement: React Projects list JSON is authenticated, exact, and bounded
The existing authenticated projects JSON handoff SHALL additionally project the archived connected projects and the Local Runner enablement flag, so the frontend can render the canonical Projects list without recomputing project rules in the browser. Both values SHALL derive from the existing backend project listings and settings flag rather than a parallel computation. The existing active-projects projection SHALL be unchanged so current consumers are unaffected.

#### Scenario: Projects JSON requires portal auth
- **WHEN** an unauthenticated caller requests the projects JSON handoff while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary
- **AND** it SHALL NOT return project data, including connected project root paths

#### Scenario: Projects JSON carries archived projects and Local Runner state
- **WHEN** an authenticated operator requests the projects JSON handoff
- **THEN** the response SHALL include the existing active `projects` array unchanged, an `archived_projects` array, and `local_runner_enabled`
- **AND** each archived row SHALL contain only `id`, name, root path, sanitized capability state, and the archive timestamp
- **AND** absent optional values SHALL be typed `null` rather than fabricated defaults

#### Scenario: Projects JSON derives from the single backend project listing
- **WHEN** an authenticated operator requests the projects JSON handoff
- **THEN** the active projects, archived projects, capability states, and Local Runner enablement SHALL be read from the existing backend project listings and settings flag
- **AND** the endpoint SHALL NOT recompute those values independently of those listings

#### Scenario: Projects JSON does not expose raw internal records
- **WHEN** an authenticated operator requests the projects JSON handoff
- **THEN** capability reasons SHALL be bounded by the existing evidence-safety helper
- **AND** the response SHALL NOT expose adapter configuration, secret values, raw exception text, or raw Worker evidence payloads

#### Scenario: Existing consumers are unaffected
- **WHEN** the React board, project workspace, or Project Task History requests the projects JSON handoff
- **THEN** the existing `projects` array SHALL retain its current fields, ordering, and task counts
- **AND** the added fields SHALL NOT change those consumers' behavior

### Requirement: React Projects list navigates inside the shell
React SHALL render the Projects list inside the shared Portal chrome on the canonical `/projects` URL when the complete build is available, and that URL SHALL return the missing-build recovery response when the build is missing or partial. The view SHALL preserve the open-local-repo form, the Local-Runner-disabled notice, per-project capability, project entry cards, Archive, and the archived list with Restore.

#### Scenario: Built canonical route opens React Projects in-shell
- **WHEN** an authenticated operator opens `/projects` while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell and render the Projects list inside the full Portal chrome
- **AND** React SHALL request the authenticated projects JSON for its active projects, archived projects, capability, and Local Runner state

#### Scenario: Missing or partial build returns the recovery response at canonical Projects
- **WHEN** an authenticated operator opens `/projects` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** it SHALL NOT return a blank shell or redirect to an alternate URL

#### Scenario: Project entry cards open the React workspace
- **WHEN** an authenticated operator selects an active project from the React Projects list
- **THEN** the shell SHALL open that project's React workspace without a full-page transition
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

## ADDED Requirements

### Requirement: React is the default authenticated landing
The normal Portal landing SHALL be the React dashboard at the canonical `/dashboard`, unconditionally. The landing decision SHALL NOT inspect build availability, because no server-rendered destination remains to divert to; a missing or partial build SHALL surface as the missing-build recovery response at `/dashboard` rather than as a different landing target. React route ownership SHALL include `/dashboard`, `/projects`, `/projects/{id}`, `/projects/{id}/board`, `/sessions`, `/sessions/{session_id}`, `/task-breakdowns/{breakdown_id}/review`, `/projects/{id}/task-history`, `/alarms`, `/setup`, and the destination Settings routes `/settings/control-plane`, `/settings/budget`, `/settings/project`, and `/settings/workers`.

#### Scenario: Auth-disabled local root opens the React dashboard
- **WHEN** portal auth is not required and an operator opens `/`
- **THEN** the system SHALL redirect to `/dashboard`

#### Scenario: Successful login opens the React dashboard
- **WHEN** portal auth is required and an operator submits a valid portal token
- **THEN** the system SHALL preserve the existing signed cookie behavior
- **AND** the successful login response SHALL redirect to `/dashboard`

#### Scenario: Authenticated root opens the React dashboard
- **WHEN** portal auth is required and an authenticated operator opens `/`
- **THEN** the system SHALL redirect to `/dashboard`

#### Scenario: Unauthenticated shared root still requires login
- **WHEN** portal auth is required and an unauthenticated operator opens `/`
- **THEN** the system SHALL redirect to `/login`
- **AND** build availability SHALL NOT bypass the existing authentication boundary

#### Scenario: Auth-disabled login and logout use the normal landing
- **WHEN** portal auth is not required and an operator opens `/login`, submits a well-formed `/login` request containing the existing required token form field, or submits `/logout`
- **THEN** the system SHALL preserve existing harmless login/logout behavior
- **AND** it SHALL redirect to `/dashboard`

#### Scenario: Landing does not inspect build availability
- **WHEN** a normal landing decision occurs while the React index is missing or one or more referenced local React assets are missing or invalid
- **THEN** the system SHALL still redirect to `/dashboard`
- **AND** `/dashboard` SHALL return the missing-build recovery response
- **AND** the operator SHALL NOT be diverted to a server-rendered landing, which no longer exists

#### Scenario: Login remains reachable when the build is missing
- **WHEN** the React build is missing or partial and an operator opens `/login` while portal auth is required
- **THEN** the server-rendered login page SHALL render normally
- **AND** it SHALL remain the operator's way into the Portal independent of build state

## REMOVED Requirements

### Requirement: React is the build-aware default authenticated landing
**Reason**: The requirement's premise was that a server-rendered first-project or `/projects` landing exists to fall back to when the build is missing or partial. This change deletes those pages, so the build-aware branch has no destination and the requirement's title asserts the opposite of the new behavior. Its scenarios "Missing React index falls back to Jinja landing", "Partial React build falls back to Jinja landing", "Fallback landing on the canonical Projects route serves Jinja", "Missing or partial build keeps canonical Sessions in Jinja", "Missing or partial build keeps canonical Task Breakdown Review in Jinja", and "Non-migrated and fallback Jinja routes remain reachable" describe pages that no longer exist, and its "Explicit React deep link retains clear missing-build behavior" scenario requires the recovery response to carry "a usable Jinja fallback link" that would now point at the recovery response itself.

**Migration**: Replaced by "React is the default authenticated landing", which keeps every still-true scenario — auth-disabled root, successful login, authenticated root, unauthenticated root, and auth-disabled login/logout all still land on `/dashboard` — and replaces the three fallback scenarios with "Landing does not inspect build availability". The missing-build behavior those scenarios governed is now specified once, per route, by the recovery-response scenarios on each surface's requirement. Operators who relied on a server-rendered landing when the frontend was unbuilt must build the frontend; the recovery response names the command, and `/login` remains server-rendered.
