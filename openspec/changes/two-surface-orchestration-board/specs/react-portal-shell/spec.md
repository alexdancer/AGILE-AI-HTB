## MODIFIED Requirements

### Requirement: React owns only the migrated project surfaces
The React Portal shell SHALL own its dashboard home, the Projects list, selected project Pipeline, Execution Floor, Sessions list, Session Report, Task Breakdown Review, Project Task History, and the Alarms inbox. No server-rendered equivalent of those surfaces SHALL remain. The selected project Pipeline SHALL preserve the existing project overview's identity, profile, readiness, actionable summary, archive safety, and workflow navigation. The canonical `/dashboard`, `/projects`, `/projects/{project_id}`, `/projects/{project_id}/floor`, `/sessions`, `/sessions/{session_id}`, `/task-breakdowns/{breakdown_id}/review`, `/projects/{project_id}/task-history`, and `/alarms` routes SHALL serve React when the complete frontend build is available and SHALL return the missing-build recovery response otherwise. Legacy `/projects/{project_id}/board`, `/app/projects/{project_id}`, and `/app/projects/{project_id}/board` SHALL permanently redirect to `/projects/{project_id}`; `/app/projects/{project_id}/floor` SHALL permanently redirect to `/projects/{project_id}/floor`.

#### Scenario: Unknown React paths are not claimed
- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{project_id}`, `/app/projects/{project_id}/board`, or `/app/projects/{project_id}/floor`
- **THEN** the system SHALL return not found instead of silently redirecting or rendering a React surface

#### Scenario: Dashboard opens in React shell
- **WHEN** an authenticated operator opens the canonical `/dashboard` while the complete build is available
- **THEN** the React shell SHALL show dashboard-equivalent operator state using data supplied by FastAPI

#### Scenario: Projects list opens in React shell
- **WHEN** an authenticated operator opens the canonical `/projects` while the complete build is available
- **THEN** the React shell SHALL show the connected and archived project lists using data supplied by FastAPI

#### Scenario: Global board shim targets the Pipeline
- **WHEN** an authenticated operator opens `/board`
- **THEN** the system SHALL redirect onto the first connected project's Pipeline at `/projects/{project_id}`, or onto `/projects` when no project is connected
- **AND** it SHALL preserve bounded validation query parameters through the redirect
- **AND** this change SHALL NOT give `/board` a separate React or server-rendered view

#### Scenario: Built canonical Pipeline opens in React
- **WHEN** an authenticated operator opens `/projects/{project_id}` for an existing connected project while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the project Pipeline inside the shared Portal chrome

#### Scenario: Built canonical Execution Floor opens in React
- **WHEN** an authenticated operator opens `/projects/{project_id}/floor` for an existing active connected project while the complete React build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the project Execution Floor inside the shared Portal chrome

#### Scenario: Missing or partial build returns the recovery response at canonical project surfaces
- **WHEN** an authenticated operator opens `/projects/{project_id}` or `/projects/{project_id}/floor` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at that same canonical URL
- **AND** it SHALL NOT return a blank shell or redirect to an alternate server-rendered surface

#### Scenario: Legacy project board redirects to Pipeline
- **WHEN** an authenticated operator opens `/projects/{project_id}/board` or `/app/projects/{project_id}/board`
- **THEN** FastAPI SHALL permanently redirect to `/projects/{project_id}` while preserving bounded validation query parameters
- **AND** it SHALL NOT serve a duplicate board surface

#### Scenario: Unknown project is rejected before the shell is served
- **WHEN** an authenticated operator opens `/projects/{project_id}`, `/projects/{project_id}/floor`, or `/projects/{project_id}/board` for a project that does not exist
- **THEN** FastAPI SHALL return its existing not-found response regardless of build availability
- **AND** it SHALL NOT serve the React shell or the recovery response for an unknown project

#### Scenario: Active project Pipeline opens with full overview state
- **WHEN** an authenticated operator opens the canonical `/projects/{project_id}` for an active connected project
- **THEN** React SHALL show project identity, capability/readiness and reasons, canonical task counts, actionable attention state, and repository profile fields using authenticated FastAPI data
- **AND** planning and intake actions SHALL remain on the Pipeline
- **AND** the surface SHALL link to `/projects/{project_id}/floor` for active execution and Review
- **AND** Worker setup and Project settings SHALL remain ordinary full-page links
- **AND** task history SHALL use the canonical `/projects/{project_id}/task-history` link
- **AND** Sessions SHALL use the canonical `/sessions` link

#### Scenario: Archived project Pipeline is restore-first
- **WHEN** an authenticated operator opens the canonical `/projects/{project_id}` for an archived connected project
- **THEN** React SHALL show an archived warning, Restore action, and retained task-history/session evidence links
- **AND** React SHALL suppress active Floor and launch entry points until refreshed backend state reports the project restored

#### Scenario: Project task workflow completes across Pipeline and Floor
- **WHEN** an authenticated operator uses the canonical Pipeline and Execution Floor for an active connected project
- **THEN** the React shell SHALL show project-scoped planning, task intake, Estimated work, active Worker Runs, Review, recently-finished evidence, queue controls, and bounded task evidence using authenticated FastAPI data and actions
- **AND** backend validation SHALL remain authoritative for every workflow decision

#### Scenario: Archived Execution Floor routes the operator to Restore
- **WHEN** an authenticated operator opens `/projects/{project_id}/floor` for an archived project while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell
- **AND** React SHALL clearly identify the archived state and provide a route to `/projects/{project_id}` for Restore
- **AND** the surface SHALL not present launch controls

#### Scenario: Built canonical Sessions list opens in React
- **WHEN** an authenticated operator opens `/sessions` while the complete build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the Sessions list inside the shared Portal chrome

#### Scenario: Built canonical Session Report opens in React
- **WHEN** an authenticated operator opens `/sessions/{session_id}` for an existing session while the complete build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the Session Report as the only audit-inspection surface

#### Scenario: Missing or partial build returns the recovery response at canonical Sessions
- **WHEN** an authenticated operator opens `/sessions` or `/sessions/{session_id}` while the React build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** session evidence SHALL be unavailable until the frontend is built, rather than diverting to a server-rendered sessions list or report

#### Scenario: Built canonical Task Breakdown Review opens in React
- **WHEN** an authenticated operator opens `/task-breakdowns/{breakdown_id}/review` for an existing review while the complete build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the complete review/edit/recovery workflow inside the shared Portal chrome
- **AND** project-bound reviews SHALL retain the selected project's Pipeline, Floor, and Needs You navigation context

#### Scenario: Built canonical Project Task History opens in React
- **WHEN** an authenticated operator opens `/projects/{project_id}/task-history` for an existing project while the complete build is available
- **THEN** FastAPI SHALL return the React shell for that canonical URL
- **AND** React SHALL render the Project Task History as the only archive-inspection and restore surface

#### Scenario: Built canonical Alarms inbox opens in React
- **WHEN** an authenticated operator opens `/alarms` while the complete build is available
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
- **WHEN** the React Pipeline, Execution Floor, or Project Task History cannot load its state and renders an error
- **THEN** it SHALL render a sanitized error rather than raw backend detail
- **AND** it SHALL NOT link to a server-rendered equivalent, which no longer exists

### Requirement: React uses authenticated JSON handoff endpoints
The React Portal shell SHALL load dashboard, project Pipeline and Execution Floor, Sessions list, Session Report, Task Breakdown Review, and Alarms inbox state through authenticated FastAPI JSON endpoints that reuse existing view helpers and domain logic. The workspace endpoint SHALL return the exact bounded contract defined below, and existing Restore, task, queue, review, and breakdown-review actions SHALL provide explicit JSON outcomes only to callers that negotiate `application/json` while preserving HTML redirects. Session, Task Breakdown, and Alarms handoffs SHALL be bounded, redacted, and paged where collections can grow.

#### Scenario: React state requires portal auth
- **WHEN** an unauthenticated request calls a React dashboard, project workspace, Pipeline/Floor board state, Sessions, Session Report, report evidence-page, full-text continuation, report-freshness, Task Breakdown Review, breakdown evidence-page, or breakdown full-text endpoint while portal auth is required
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
- **AND** `counts` SHALL contain exactly the canonical `Estimated`, `Running`, `Review`, and `Done` non-negative integer fields
- **AND** each attention action SHALL contain exactly `label`, `detail`, `href`, and `tone`
- **AND** `controls` SHALL contain exactly `can_open_board` and `can_restore`
- **AND** `links` SHALL contain exactly `board_href`, `floor_href`, `task_history_href`, `sessions_href`, `worker_setup_href`, `project_settings_href`, and `restore_href`

#### Scenario: Workspace JSON applies fixed bounds and safe defaults
- **WHEN** project/profile/capability/helper data contains long, missing, or malformed values
- **THEN** strings SHALL be sanitized/redacted before truncation using the design bounds
- **AND** capability reasons, profile hints/docs, and attention actions SHALL use the design item-count and per-item bounds
- **AND** wrong nested types SHALL become typed `null`, empty-list, empty-string, `false`, or zero defaults instead of producing a server error
- **AND** raw project metadata, backend ids/configuration, adapter state, secrets, session credentials, command plans, token-ledger entries, and unknown extra keys SHALL NOT be serialized

#### Scenario: Workspace links follow fixed route ownership
- **WHEN** FastAPI projects workspace links and attention actions
- **THEN** active `board_href` and Pipeline-targeting attention hrefs SHALL be exactly `/projects/{project_id}`
- **AND** active `floor_href` SHALL be exactly `/projects/{project_id}/floor`
- **AND** task history, Sessions, Worker setup, and Project settings hrefs SHALL use their existing canonical routes
- **AND** unknown helper hrefs SHALL be dropped
- **AND** archived projects SHALL return `can_open_board: false`, `board_href: null`, `floor_href: null`, `can_restore: true`, and `restore_href: /projects/{project_id}/restore`

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
