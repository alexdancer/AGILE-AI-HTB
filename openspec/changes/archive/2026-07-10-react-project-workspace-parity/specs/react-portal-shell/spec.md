## MODIFIED Requirements

### Requirement: React owns only the migrated project surfaces
The React Portal shell SHALL own its dashboard home, selected project workspace, and project board workflow while existing Jinja pages remain available for non-migrated workflows and as dashboard/board/workspace fallback. The selected React project workspace SHALL preserve the existing project overview's identity, profile, readiness, actionable summary, archive safety, and workflow navigation.

#### Scenario: Unknown React paths are not claimed
- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{project_id}`, or `/app/projects/{project_id}/board`
- **THEN** the system SHALL return not found instead of silently rendering a React surface

#### Scenario: Dashboard opens in React shell
- **WHEN** an authenticated operator explicitly opens `/app`
- **THEN** the React shell SHALL show dashboard-equivalent operator state using data supplied by FastAPI
- **AND** the existing Jinja `/dashboard` route SHALL remain reachable as a fallback

#### Scenario: Active project workspace opens with full overview state
- **WHEN** an authenticated operator opens `/app/projects/{project_id}` for an active connected project
- **THEN** React SHALL show project identity, capability/readiness and reasons, canonical task counts, actionable attention state, and repository profile fields using authenticated FastAPI data
- **AND** board-targeting actions SHALL use `/app/projects/{project_id}/board`
- **AND** task history, Sessions, Worker setup, and Project settings SHALL remain ordinary full-page links

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

#### Scenario: Jinja surfaces remain reachable as fallback
- **WHEN** an operator needs the server-rendered workspace or board, Task Breakdown Review, task history, session/report evidence, setup, settings, alarms, login, or another non-migrated Portal workflow
- **THEN** the existing FastAPI/Jinja page SHALL remain reachable
- **AND** the React board SHALL not require the Jinja board to complete its normal in-board workflow

### Requirement: React uses authenticated JSON handoff endpoints
The React Portal shell SHALL load dashboard, project workspace, and project board state through authenticated FastAPI JSON endpoints that reuse existing view helpers and domain logic. The workspace endpoint SHALL return the exact bounded contract defined below, and the existing Restore action SHALL provide explicit JSON outcomes only to callers that negotiate `application/json` while preserving HTML redirects.

#### Scenario: React state requires portal auth
- **WHEN** an unauthenticated request calls a React dashboard, project workspace, or board JSON endpoint while portal auth is required
- **THEN** the system SHALL reject the request using the existing portal authentication boundary

#### Scenario: JSON state reuses existing Portal behavior
- **WHEN** React requests dashboard or project state
- **THEN** FastAPI SHALL derive the response from existing dashboard, project, board, Worker readiness, budget, run automation, alarm, and review evidence helpers where those helpers already exist
- **AND** it SHALL NOT duplicate launch guardrail, estimation, Worker Run, budget, alarm-resolution, archive/restore, or review-disposition rules in frontend code

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
- **THEN** active `board_href` and board-targeting attention hrefs SHALL be exactly `/app/projects/{project_id}/board`
- **AND** task history, Sessions, Worker setup, and Project settings hrefs SHALL use their existing Jinja routes
- **AND** unknown helper hrefs SHALL be dropped
- **AND** archived projects SHALL return `can_open_board: false`, `board_href: null`, `can_restore: true`, and `restore_href: /projects/{project_id}/restore`

#### Scenario: React Restore receives fixed success outcome
- **WHEN** React posts to `/projects/{project_id}/restore` with `Accept: application/json` for an archived or already-active project
- **THEN** the response SHALL be `200` JSON with exactly `ok`, `error`, `next_href`, `retry_href`, and `project`
- **AND** it SHALL contain `ok: true`, `error: null`, `next_href: /app/projects/{project_id}`, `retry_href: null`, and project fields exactly `id` and `archived: false`
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
- **WHEN** React submits task intake, estimate, launch, refresh, queue, review, archive, dismiss, or block actions
- **THEN** the request SHALL call existing FastAPI action paths or thin JSON wrappers around those paths
- **AND** backend validation SHALL remain authoritative for project binding, launch guardrails, budget acknowledgement, native usage acknowledgement, and review disposition