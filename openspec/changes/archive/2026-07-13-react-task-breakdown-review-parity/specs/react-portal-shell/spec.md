## MODIFIED Requirements

### Requirement: React owns only the migrated project surfaces
The React Portal shell SHALL own its dashboard home, selected project workspace, project board workflow, Sessions list, Session Report, and Task Breakdown Review while existing Jinja pages remain available for non-migrated workflows and as build-aware fallback for migrated surfaces. The selected React project workspace SHALL preserve the existing project overview's identity, profile, readiness, actionable summary, archive safety, and workflow navigation. The canonical `/sessions`, `/sessions/{session_id}`, and `/task-breakdowns/{breakdown_id}/review` routes SHALL select React only when the complete frontend build is available.

#### Scenario: Unknown React paths are not claimed
- **WHEN** an operator opens a path under `/app` other than `/app`, `/app/projects/{project_id}`, or `/app/projects/{project_id}/board`
- **THEN** the system SHALL return not found instead of silently rendering a React surface
- **AND** this change SHALL NOT add `/app/sessions`, `/app/sessions/{session_id}`, or `/app/task-breakdowns/{breakdown_id}/review` aliases

#### Scenario: Dashboard opens in React shell
- **WHEN** an authenticated operator explicitly opens `/app`
- **THEN** the React shell SHALL show dashboard-equivalent operator state using data supplied by FastAPI
- **AND** the existing Jinja `/dashboard` route SHALL remain reachable as a fallback

#### Scenario: Active project workspace opens with full overview state
- **WHEN** an authenticated operator opens `/app/projects/{project_id}` for an active connected project
- **THEN** React SHALL show project identity, capability/readiness and reasons, canonical task counts, actionable attention state, and repository profile fields using authenticated FastAPI data
- **AND** board-targeting actions SHALL use `/app/projects/{project_id}/board`
- **AND** task history, Worker setup, and Project settings SHALL remain ordinary full-page links
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

#### Scenario: Jinja surfaces remain reachable as fallback
- **WHEN** an operator needs a missing/partial-build fallback for a migrated surface or opens task history, setup, settings, alarms, login, or another non-migrated Portal workflow
- **THEN** the corresponding existing FastAPI/Jinja page SHALL remain reachable
- **AND** the React board SHALL not require the Jinja board to complete its normal in-board workflow

### Requirement: React uses authenticated JSON handoff endpoints
The React Portal shell SHALL load dashboard, project workspace, project board, Sessions list, Session Report, and Task Breakdown Review state through authenticated FastAPI JSON endpoints that reuse existing view helpers and domain logic. The workspace endpoint SHALL return the exact bounded contract defined below, and existing Restore, board, and breakdown-review actions SHALL provide explicit JSON outcomes only to callers that negotiate `application/json` while preserving HTML redirects. Session and Task Breakdown handoffs SHALL be bounded, redacted, and paged where collections can grow.

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
- **THEN** active `board_href` and board-targeting attention hrefs SHALL be exactly `/app/projects/{project_id}/board`
- **AND** task history, Sessions, Worker setup, and Project settings hrefs SHALL use their existing canonical routes
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
- **WHEN** React submits task intake, estimate, launch, refresh, queue, review, archive, dismiss, block, Task Breakdown Accept, Retry, or Manual Candidate actions
- **THEN** the request SHALL call existing FastAPI action paths or thin JSON wrappers around those paths
- **AND** backend validation SHALL remain authoritative for project binding, candidate normalization, Task Estimation, launch guardrails, budget acknowledgement, native usage acknowledgement, and review disposition

### Requirement: React is the build-aware default authenticated landing
The normal Portal landing SHALL use the React dashboard at `/app` when the complete built React shell is available. The system SHALL validate the React index and all referenced local React assets before choosing `/app`; when that validation fails, the normal landing SHALL remain the existing server-rendered first-project or `/projects` route. This promotion SHALL NOT remove explicit Jinja fallback routes. React route ownership SHALL include `/app`, `/app/projects/{id}`, `/app/projects/{id}/board`, `/sessions`, `/sessions/{session_id}`, and `/task-breakdowns/{breakdown_id}/review` only for the migrated surfaces defined by this specification.

#### Scenario: Auth-disabled local root opens built React dashboard
- **WHEN** portal auth is not required and an operator opens `/` while the complete React build is available
- **THEN** the system SHALL redirect to `/app`
- **AND** the React shell SHALL render its dashboard inside the full Portal chrome

#### Scenario: Successful login opens built React dashboard
- **WHEN** portal auth is required and an operator submits a valid portal token while the complete React build is available
- **THEN** the system SHALL preserve the existing signed cookie behavior
- **AND** the successful login response SHALL redirect to `/app`

#### Scenario: Authenticated root opens built React dashboard
- **WHEN** portal auth is required and an authenticated operator opens `/` while the complete React build is available
- **THEN** the system SHALL redirect to `/app`

#### Scenario: Unauthenticated shared root still requires login
- **WHEN** portal auth is required and an unauthenticated operator opens `/`
- **THEN** the system SHALL redirect to `/login`
- **AND** build availability SHALL NOT bypass the existing authentication boundary

#### Scenario: Auth-disabled login and logout use normal landing
- **WHEN** portal auth is not required and an operator opens `/login`, submits a well-formed `/login` request containing the existing required token form field, or submits `/logout`
- **THEN** the system SHALL preserve existing harmless login/logout behavior
- **AND** it SHALL redirect to `/app` when the complete React build is available

#### Scenario: Missing React index falls back to Jinja landing
- **WHEN** a normal landing decision occurs and the React index is missing
- **THEN** the system SHALL redirect to the existing server-rendered first-project route when a connected project exists, otherwise `/projects`
- **AND** the operator SHALL NOT receive a blank shell or missing-build `503` as the default landing

#### Scenario: Partial React build falls back to Jinja landing
- **WHEN** the React index exists but one or more referenced local React assets are missing or invalid
- **THEN** the normal landing SHALL use the existing server-rendered first-project or `/projects` route
- **AND** the system SHALL NOT promote the partial shell

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
- **WHEN** an operator on the default React shell follows a link to Alarms, Setup, Settings, task history, or an explicit server-rendered fallback surface
- **THEN** the existing FastAPI/Jinja route SHALL remain reachable through ordinary full-page navigation
- **AND** no React client route SHALL claim that non-migrated path

### Requirement: React shell navigates client-side between its surfaces
The React Portal shell SHALL let operators move between its dashboard home, project workspace, project board, Sessions, Session Report, and Task Breakdown Review without manual URL entry, while deep links to React-owned routes still resolve on a full page load.

#### Scenario: Selecting a project opens its workspace in-shell
- **WHEN** an operator selects a project from the React dashboard or sidebar
- **THEN** the shell SHALL open that project's workspace without the operator typing a URL

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
- **WHEN** an operator loads or refreshes a React-owned route such as the dashboard, project workspace, board, Sessions, Session Report, or Task Breakdown Review URL directly
- **THEN** the system SHALL serve the React shell for that existing resource route when the complete build is available

## ADDED Requirements

### Requirement: React Task Breakdown Review JSON is exact, bounded, and complete
The system SHALL expose authenticated read-only `/api/task-breakdowns/{breakdown_id}/review` state derived from the shared Task Breakdown Review context, with exact allowlisted fields, bounded previews, pageable collections, and generated access to complete redacted overflow.

#### Scenario: Review response uses exact top-level and review keys
- **WHEN** an authenticated operator requests an existing Task Breakdown Review projection
- **THEN** the response SHALL contain exactly `review`, `candidates`, `context`, `repo_context`, `controls`, and `links`
- **AND** `review` SHALL contain exactly `id`, `status`, `decision`, `model`, `session_id`, `session_href`, `rationale`, `source_text`, `failure_type`, `failure_message`, and `created_task_ids`
- **AND** `created_task_ids` SHALL be a bounded pageable collection of Task-id text evidence rather than an unbounded array or invented Task-detail links
- **AND** `controls` SHALL contain exactly `can_accept`, `can_retry`, and `can_create_manual_candidate`
- **AND** `links` SHALL contain exactly `self_href`, `api_href`, `board_href`, `accept_href`, `retry_href`, and `manual_href`
- **AND** every key SHALL use the exact JSON type, nullability, malformed default, bound, continuation selector, and derivation in the design's normative field matrix
- **AND** the response SHALL use `Cache-Control: no-store`

#### Scenario: Review controls derive only from authoritative status
- **WHEN** FastAPI projects review controls and action links
- **THEN** `can_accept` SHALL be true exactly for a normalized proposed review with at least one candidate, except while the durable record holds the internal `accepting` claim state
- **AND** `can_retry` and `can_create_manual_candidate` SHALL be true exactly for a normalized failed review
- **AND** an internal `accepting` claim SHALL normalize to the proposed read-only shape while all three mutation controls remain false
- **AND** accepted reviews SHALL expose no mutation hrefs

#### Scenario: Candidate projection uses exact fields
- **WHEN** the review projects candidates
- **THEN** `candidates` SHALL contain exactly `items` and `pagination`
- **AND** each candidate item SHALL contain exactly `index`, `accepted_by_default`, `kind`, `execution_mode`, `title`, `objective`, `prompt`, `acceptance_criteria`, `proof`, `hitl_reason`, `constraints`, `why_this_task_exists`, `why_not_smaller`, `why_not_larger`, `dependencies`, and `likely_entry_points`
- **AND** candidate text fields, including newline-joined list fields, SHALL use bounded-text objects exactly `preview`, `truncated`, and `full_href`
- **AND** `kind` and `execution_mode` SHALL use the fixed enums and normalization in the design rather than bounded text
- **AND** `accepted_by_default` SHALL be true for every candidate in a proposed review regardless of malformed persisted boolean-like values, matching Jinja's checked-by-default behavior
- **AND** accepted-review candidates SHALL be read-only with `accepted_by_default: false`
- **AND** persisted candidate ordinal SHALL remain stable across pages

#### Scenario: Preserved context uses exact fields
- **WHEN** the review projects source-contract context
- **THEN** `context` SHALL contain exactly `global_contract_summary`, `global_constraints`, `verification`, `rejected_items`, `non_goals`, and `recommended_sequence`
- **AND** each collection SHALL contain exactly `items` and `pagination`
- **AND** each rejected item SHALL contain exactly bounded-text `text` and `reason`
- **AND** other context collection items SHALL be bounded-text objects

#### Scenario: Repo Context projection is exact and safe
- **WHEN** the review has stored Repo Context evidence
- **THEN** `repo_context` SHALL contain exactly `available`, `source`, `text_chars`, `documents`, `manifests`, `entrypoints`, `test_commands`, and `tracked_files_sample`
- **AND** `source` SHALL be nullable bounded text and every Repo Context collection item SHALL be bounded text using the design's exact selectors
- **AND** each Repo Context collection SHALL contain exactly `items` and `pagination`
- **AND** project root, raw file contents, secret-bearing metadata, and unknown keys SHALL NOT serialize
- **AND** absent or malformed Repo Context evidence SHALL produce typed unavailable/empty defaults rather than a server error

#### Scenario: Review projection applies exact bounds and malformed defaults
- **WHEN** review data contains long, missing, malformed, boolean-as-number, or unknown values
- **THEN** FastAPI SHALL redact/sanitize before applying the design's exact field and list bounds
- **AND** every field SHALL use the exact per-path malformed/default rule in the normative matrix rather than a generic default that could change candidate selection
- **AND** non-string `non_goals` and `recommended_sequence` items SHALL project as empty bounded text while preserving their ordinals
- **AND** raw intake metadata, source hashes, project root/profile, raw provider requests, token rows, guardrail overrides, secrets, and unknown extra fields SHALL NOT serialize

#### Scenario: Review redaction is complete before previewing
- **WHEN** projected free text or Repo Context evidence contains opaque values under exact generic `token` or other credential/PAT names, cookies, authorization or `X-Auth` headers, nested headers/environment/metadata, bearer/basic values, URI credentials, PEM keys, JWTs, provider-token families, or secret-named `.env*`, `credentials.*`, or equivalent paths
- **THEN** FastAPI SHALL apply the design's case/separator-insensitive key, value, token-family, and path policy to the complete value before truncation
- **AND** the same complete redacted value SHALL back preview and full continuation
- **AND** safe surrounding text SHALL remain visible while sensitive values become `[REDACTED]`

#### Scenario: Links are generated from exact route allowlist
- **WHEN** FastAPI projects review links
- **THEN** self/API/action links SHALL use only the current breakdown id, Session links only the encoded stored session id, and board links only the existing canonical project/global board helper
- **AND** arbitrary persisted hrefs SHALL be ignored

#### Scenario: Unknown review is rejected
- **WHEN** an authenticated operator requests the review projection for an unknown breakdown id
- **THEN** FastAPI SHALL return `404` with sanitized `Task breakdown not found` evidence

### Requirement: Task Breakdown Review evidence pages preserve bounded overflow
The system SHALL expose authenticated review evidence pages at `/api/task-breakdowns/{breakdown_id}/review/evidence/{collection_id}` for the exact collection ids `candidates`, `created-task-ids`, `global-constraints`, `verification`, `rejected-items`, `non-goals`, `recommended-sequence`, `repo-documents`, `repo-manifests`, `repo-entrypoints`, `repo-test-commands`, and `repo-tracked-files`.

#### Scenario: Review evidence page is bounded and ordered
- **WHEN** an authenticated operator requests an allowlisted collection
- **THEN** the response SHALL contain exactly `items` and `pagination`
- **AND** pagination SHALL contain exactly `offset`, `limit`, `total`, `has_more`, and generated nullable `next_href`
- **AND** candidate pages SHALL default to 20 and reject limits above 50
- **AND** other pages SHALL default to 50 and reject limits above 100
- **AND** every collection SHALL preserve persisted ordinal ordering
- **AND** every JSON evidence response SHALL use `Cache-Control: no-store`

#### Scenario: Review evidence query validation is deterministic
- **WHEN** `offset` or `limit` is malformed, offset is negative, limit is below one, or limit exceeds the collection maximum
- **THEN** FastAPI SHALL return `422`
- **AND** it SHALL NOT silently clamp or reinterpret the query

#### Scenario: Unknown review evidence selector is rejected
- **WHEN** a caller requests a collection outside the exact allowlist
- **THEN** FastAPI SHALL return `404`
- **AND** it SHALL NOT interpret the selector as a DB field, object path, table, or filesystem path

### Requirement: Truncated Task Breakdown text has authenticated full continuation
Every bounded review string that omits redacted content SHALL emit a generated same-review `/api/task-breakdowns/{breakdown_id}/review/text/{text_id}` continuation selected from the design's exact fixed/dynamic allowlist.

#### Scenario: Full review text returns complete redacted value
- **WHEN** an authenticated operator follows a generated `full_href`
- **THEN** FastAPI SHALL return the complete redacted value as `text/plain; charset=utf-8` with `Cache-Control: no-store`
- **AND** the response SHALL not contain unredacted credentials, raw provider payloads, project-root metadata, or unknown fields

#### Scenario: Unknown review text selector is rejected
- **WHEN** a caller supplies a text id outside the exact fixed/dynamic allowlist for that review
- **THEN** FastAPI SHALL return `404`
- **AND** it SHALL NOT interpret the id as a file path, database field, table, or arbitrary object path

### Requirement: React negotiates fixed Task Breakdown action outcomes
The existing Accept, Retry, and Manual Candidate paths SHALL map the domain outcomes owned by `task-breakdown-review` into the design's exact transport table only when `application/json` is explicitly negotiated. React SHALL consume that transport without reimplementing acceptance, status, Task creation, recovery, or idempotency rules.

#### Scenario: Negotiated envelope has exact types
- **WHEN** a Task Breakdown action explicitly negotiates `application/json`
- **THEN** the response SHALL contain exactly `ok`, `error`, `next_href`, `retry_href`, `breakdown_id`, `status`, and `created_task_count`
- **AND** every field SHALL use the exact type, nullability, fixed safe error text, generated href, and value defined by the normative outcome table
- **AND** submitted secret values SHALL never be reflected in `error`

#### Scenario: Accept success maps to board navigation
- **WHEN** the backend domain acceptance succeeds for a proposed review
- **THEN** transport SHALL return the table's `200` accepted outcome with the full durable created Task count and canonical board `next_href`
- **AND** React SHALL clear dirty state before navigating

#### Scenario: Accepted mutation replay maps idempotently
- **WHEN** the backend reports that Accept, Retry, or Manual Candidate targeted an already accepted review
- **THEN** transport SHALL return the table's `200` accepted outcome with the existing full created Task count and canonical board `next_href`
- **AND** React SHALL navigate without attempting to recreate or rewrite domain state

#### Scenario: Failed-review conflict and invalid edits preserve draft
- **WHEN** the backend rejects Accept because the review is failed or candidate/global edits are invalid
- **THEN** transport SHALL return the table's exact `409` or `422` outcome with fixed safe error, current id/status, zero created count, `next_href: null`, and canonical self `retry_href`
- **AND** React SHALL preserve local edits and SHALL not refetch

#### Scenario: Edited values use explicit request maxima and presence semantics
- **WHEN** React submits edited Accept or Manual Candidate fields
- **THEN** FastAPI SHALL enforce the exact per-field maxima defined in the design while allowing omitted untouched fields to retain persisted originals
- **AND** present empty optional/list fields SHALL clear their values while present empty required fields fail domain validation
- **AND** loading redacted full text without editing SHALL leave the field omitted and preserve its persisted value, while a later actual edit SHALL submit the complete edited redacted value
- **AND** a handled failure SHALL map to the exact fixed `422` outcome without persisting partial acceptance

#### Scenario: Retry and Manual Candidate success refetches authoritative review
- **WHEN** the backend completes Retry or Manual Candidate for a non-accepted review
- **THEN** transport SHALL return the table's exact `200` proposed-or-failed outcome with canonical self `next_href`, `retry_href: null`, and zero created count
- **AND** React SHALL clear the superseded local draft and refetch the review
- **AND** a Retry whose provider result remains failed SHALL render that authoritative failed recovery state

#### Scenario: Unknown and unexpected failures use fixed values
- **WHEN** the backend cannot find the requested review or a known-review action fails before a handled domain outcome
- **THEN** transport SHALL return the table's exact `404` or `500` envelope, including all null/current fields and fixed safe error text
- **AND** React SHALL preserve local state and SHALL not infer success

#### Scenario: HTML actions preserve representation and redirect contracts
- **WHEN** a browser form caller does not explicitly negotiate `application/json`
- **THEN** the existing form representation and `303` redirect targets SHALL remain unchanged
- **AND** the same presence-aware backend domain parser used by negotiated JSON SHALL distinguish omitted, present-empty optional, and present-empty required fields
