## MODIFIED Requirements

### Requirement: React project board provides the normal governed task loop
The React Orchestration Board SHALL present as two surfaces — a Pipeline Surface at the canonical `/projects/{project_id}` and an Execution Floor at `/projects/{project_id}/floor` — and SHALL let an authenticated operator perform the existing normal project-scoped workflow across them: submit task intake, receive estimated work or an authoritative Task Breakdown Review handoff, launch an Estimated task, refresh Running work, use Review Disposition, and archive or dismiss cards. The board SHALL NOT present a `Blocked` column; work that cannot proceed SHALL be shown in place with a Blocked Condition flag. FastAPI SHALL remain authoritative for every lifecycle transition, project-binding check, estimation, launch guardrail, Worker Run, queue, review, and archive decision.

#### Scenario: React intake creates an estimated project task
- **WHEN** an operator submits a valid short task from the Pipeline Surface
- **THEN** the system SHALL use the existing project-scoped intake and estimation behavior
- **AND** the Pipeline Surface SHALL reload authoritative board state showing the resulting task outcome

#### Scenario: React markdown intake always requires existing Task Breakdown Review
- **WHEN** an operator submits Markdown text or an uploaded Markdown file from the Pipeline Surface
- **THEN** the system SHALL preserve the existing review-first intake behavior
- **AND** the response SHALL provide the authoritative Task Breakdown Review URL
- **AND** the browser SHALL navigate to that canonical review route rather than creating unreviewed board tasks

#### Scenario: Single-task Markdown and file precedence remain intact
- **WHEN** an operator submits Markdown that the Task Breakdown Agent classifies as one coherent task, or submits both pasted text and an uploaded Markdown file
- **THEN** the system SHALL require Task Breakdown Review before creating an Estimated task
- **AND** the uploaded Markdown file SHALL remain the review source when both inputs are supplied

#### Scenario: Short non-Markdown text may estimate directly
- **WHEN** an operator submits a valid short non-Markdown task description
- **THEN** the system MAY use the existing direct project-scoped estimation behavior
- **AND** it SHALL preserve the existing project binding and estimation result semantics

#### Scenario: Work that cannot proceed keeps its position with a Blocked Condition
- **WHEN** estimation fails for a task, or an operator blocks a Review task with a reason
- **THEN** the task SHALL retain its lifecycle state and surface position
- **AND** it SHALL display a Blocked Condition reason badge rather than moving to a `Blocked` column

#### Scenario: React card actions preserve backend workflow authority
- **WHEN** an operator launches, refreshes, saves a review prompt, requests Agent Review, marks Done, blocks, archives, dismisses, runs next, starts/stops a queue, or archives Done cards from either board surface
- **THEN** the system SHALL execute the existing authoritative FastAPI action behavior
- **AND** the React client SHALL NOT directly mutate lifecycle, budget, queue, token, or review state

### Requirement: React board state is authenticated, project-scoped, and bounded
The React project-state endpoint SHALL require portal authentication, reject archived or unknown projects using existing project boundaries, and return an explicit operator-facing projection rather than raw board context, raw task metadata, or raw adapter records.

The response SHALL contain only these top-level keys: `project`, `columns`, `board_summary`, `history_href`, `board_empty_states`, `automation`, `adapters`, and `tasks_by_status`. `project` SHALL contain only `id` and `name`. `columns`, `board_empty_states`, `board_summary.counts`, `automation.counts`, and `tasks_by_status` SHALL use exactly the canonical `Estimated`, `Running`, `Review`, and `Done` keys. `board_summary` SHALL contain only `launch_ready`, `total_tasks`, `counts`, `archived_count`, and `history_total_tasks`. `automation` SHALL contain only `counts`, `eligible_count`, `queue`, and `live_refresh_enabled`; `queue` SHALL contain only `status`, `auto_agent_review`, and `latest_stop_reason`.

Each adapter SHALL contain only `id`, `name`, `is_default`, `launchable`, `allowed_models`, and `tracking`. Each task card SHALL contain only `id`, `status`, `summary`, `estimate_tokens`, `actual_tokens`, `recommended_model`, `launch_model`, `session_href`, `review_prompt`, `timeline`, `blocked_condition`, and `controls`. `blocked_condition`, when present, SHALL contain only a bounded `reason`, `origin`, and `timestamp`. `review_prompt` SHALL be bounded control state, and `timeline` SHALL contain at most the six newest bounded live-event summaries needed by Running cards. `controls` SHALL contain only launch, refresh, review, archive, dismissal, setup, manual-estimate, budget-override, and native-usage-acknowledgement fields needed by the two surfaces. Full task, launch, token, log, review, alarm, checkpoint, and repository evidence SHALL be absent from card payloads and load lazily through `session_href` into the shared Evidence Drawer.

#### Scenario: Board state remains project-scoped
- **WHEN** an authenticated operator requests React project state for `{project_id}`
- **THEN** the response SHALL contain only active tasks bound to `{project_id}`
- **AND** task counts, history link, automation state, launch controls, and Blocked Conditions SHALL refer to that same project

#### Scenario: Board projection allowlists card and adapter fields
- **WHEN** the React project-state endpoint returns task and adapter information
- **THEN** it SHALL include only fields required for Pipeline/Floor rendering, action controls, the bounded review prompt, live summaries, Blocked Conditions, and evidence links
- **AND** it SHALL NOT expose adapter configuration, verification payloads, session credentials, raw token-ledger rows, or unbounded raw task metadata

#### Scenario: Evidence is sanitized and bounded before React receives it
- **WHEN** a task has launch diagnostics, timeline events, logs, Agent Review findings, a Blocked Condition, or Worker token components
- **THEN** the React projection SHALL sanitize secret-bearing operational summaries and bound displayed text
- **AND** timeline entries SHALL include at most the newest six events
- **AND** the response SHALL preserve a session/report link for lazy deeper audit evidence when available

#### Scenario: Card limits and truncation are explicit
- **WHEN** projected card content exceeds its surface-safe limit
- **THEN** summary text SHALL contain at most 400 characters, review-prompt text at most 4,000 characters, timeline summaries at most 1,000 characters, and the timeline SHALL contain at most six items
- **AND** the corresponding required `truncated` boolean SHALL be `true` for affected bounded text
- **AND** secret redaction SHALL occur before truncation

### Requirement: React cards preserve board readability and model/token meaning
The React Pipeline and Floor SHALL render compact cards without native expandable evidence details. Card summaries SHALL distinguish estimated tokens from normalized Worker execution actuals, show actual launched Worker model as primary when available, retain routed recommendation as secondary evidence only when it differs, and open full evidence through the shared drawer.

#### Scenario: Default card remains compact and actionable
- **WHEN** an operator opens a project surface with long task or evidence content
- **THEN** each card SHALL show a bounded task summary, key estimate/model/token metadata, Blocked Condition when present, and status-appropriate primary controls
- **AND** full task text, token components, launch data, timeline, logs, review evidence, and alarms SHALL remain available through `View evidence` when a session exists

#### Scenario: Actual Worker tokens remain Worker-only
- **WHEN** a React card renders a task with authoritative Worker execution actuals
- **THEN** it SHALL display the normalized `actual_tokens` value distinctly from the estimate
- **AND** it SHALL NOT merge control-plane estimation, task-breakdown, adapter-verification, or Agent Review/reporting tokens into that value

#### Scenario: Launched model differs from routed recommendation
- **WHEN** a task has launch-model evidence different from its routed recommendation
- **THEN** the React card SHALL display the launched Worker model as the primary run model
- **AND** it SHALL display the routed recommendation as secondary estimation provenance

## ADDED Requirements

### Requirement: Card evidence opens in an Evidence Drawer
The board SHALL NOT inline full audit evidence on task cards. Selecting a card SHALL open an Evidence Drawer beside the surface that renders token evidence, the live Worker Run feed, worker output, and Agent Review findings, and the drawer SHALL fetch that evidence when it opens rather than inlining it into the board payload.

#### Scenario: Selecting a card opens the drawer
- **WHEN** an operator selects a task card with linked session evidence
- **THEN** an Evidence Drawer SHALL open beside the current surface
- **AND** it SHALL fetch the session evidence on open rather than from the board payload

#### Scenario: Drawer keeps the surface visible
- **WHEN** the Evidence Drawer is open on the Execution Floor
- **THEN** the review queue SHALL remain visible alongside the drawer
