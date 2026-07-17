## MODIFIED Requirements

### Requirement: React owns only the migrated project surfaces
The React Portal shell SHALL own its dashboard home, selected project workspace, project board workflow, Sessions list, Session Report, Task Breakdown Review, Project Task History, and the Alarms inbox while existing Jinja pages remain available for non-migrated workflows and as build-aware fallback for migrated surfaces. The selected React project workspace SHALL preserve the existing project overview's identity, profile, readiness, actionable summary, archive safety, and workflow navigation. The canonical `/sessions`, `/sessions/{session_id}`, `/task-breakdowns/{breakdown_id}/review`, `/projects/{project_id}/task-history`, and `/alarms` routes SHALL select React only when the complete frontend build is available.

#### Scenario: Unknown React paths are not claimed
- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{project_id}`, or `/app/projects/{project_id}/board`
- **THEN** the system SHALL return not found instead of silently rendering a React surface
- **AND** this change SHALL NOT add `/app/sessions`, `/app/sessions/{session_id}`, `/app/task-breakdowns/{breakdown_id}/review`, `/app/projects/{project_id}/task-history`, or `/app/alarms` aliases

#### Scenario: Dashboard opens in React shell
- **WHEN** an authenticated operator explicitly opens `/app`
- **THEN** the React shell SHALL show dashboard-equivalent operator state using data supplied by FastAPI
- **AND** the existing Jinja `/dashboard` route SHALL remain reachable as a fallback

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
- **WHEN** an operator needs a missing/partial-build fallback for a migrated surface or opens setup, settings, login, or another non-migrated Portal workflow
- **THEN** the corresponding existing FastAPI/Jinja page SHALL remain reachable
- **AND** the React board SHALL not require the Jinja board to complete its normal in-board workflow

## ADDED Requirements

### Requirement: React Alarms JSON is authenticated, exact, and bounded
FastAPI SHALL expose a new authenticated, bounded JSON handoff for the Alarms inbox that requires Portal authentication and echoes the selected filter. The response SHALL preserve every field the operator needs to triage and audit alarms without exposing unbounded payloads.

#### Scenario: Alarms handoff requires authentication
- **WHEN** an unauthenticated caller requests the authenticated React Alarms JSON handoff
- **THEN** FastAPI SHALL reject the request using the Portal authentication boundary
- **AND** SHALL NOT return alarm inbox data

#### Scenario: Alarms JSON preserves triage and audit fields
- **WHEN** an authenticated caller requests the React Alarms JSON handoff for a filter
- **THEN** the response SHALL include the bookmarkable filter options with selected state and the currently selected filter value
- **AND** each alarm entry SHALL include its id, type, severity, session id, session report link, bounded context, recommended action, `available_actions`, and — when resolved — resolved action, sanitized payload summary, and `resolved_at`
- **AND** every string field SHALL be bounded and redaction SHALL precede truncation

### Requirement: React negotiates the alarm resolve action outcome
The existing `POST /alarms/{alarm_id}/resolve` action SHALL return a bounded JSON outcome to React/JSON callers while preserving the current Jinja redirect for HTML callers. Backend validation, including the positive-cap guard for `raise_budget`, SHALL remain authoritative for both caller types.

#### Scenario: React caller receives a JSON resolve outcome
- **WHEN** a React/JSON caller submits an alarm resolve action that passes backend validation
- **THEN** FastAPI SHALL resolve the alarm using the existing authoritative behavior
- **AND** SHALL return a bounded JSON outcome sufficient for React to refresh authoritative inbox state

#### Scenario: React caller receives a sanitized rejection
- **WHEN** a React/JSON caller submits a `raise_budget` action that fails the positive-cap guard
- **THEN** FastAPI SHALL return a sanitized error outcome envelope for the caller to surface
- **AND** the alarm SHALL remain open with no budget change

#### Scenario: HTML caller keeps the redirect
- **WHEN** a browser form caller submits an alarm resolve action
- **THEN** FastAPI SHALL preserve the existing redirect back to the Jinja alarms page
- **AND** the negotiated JSON path SHALL NOT alter that HTML behavior

### Requirement: React Alarms inbox navigates inside the shell
React SHALL render the Alarms inbox inside the shared Portal chrome with bookmarkable Open/Resolved/All filters mapped to the canonical `?filter=` query, and SHALL keep links to still-non-migrated surfaces as ordinary full-page navigation.

#### Scenario: Alarms filter is bookmarkable
- **WHEN** an operator selects an inbox filter in the React Alarms view
- **THEN** the selected filter SHALL be reflected in the canonical `?filter=` query so the view is deep-linkable and restored on reload
- **AND** the React view SHALL request the matching authenticated Alarms JSON for that filter

#### Scenario: Alarms links to session evidence inside the shell
- **WHEN** an operator follows an alarm's Session Report link from the React Alarms inbox while the build is complete
- **THEN** React SHALL navigate to the canonical Session Report inside the shared Portal chrome
