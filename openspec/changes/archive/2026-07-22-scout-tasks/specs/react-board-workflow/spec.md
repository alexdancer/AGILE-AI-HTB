## MODIFIED Requirements

### Requirement: React board state is authenticated, project-scoped, and bounded
The React project-state endpoint SHALL require portal authentication, reject archived or unknown projects using existing project boundaries, and return an explicit operator-facing projection rather than raw board context, raw task metadata, or raw adapter records.

The response SHALL contain only these top-level keys: `project`, `columns`, `board_summary`, `history_href`, `board_empty_states`, `automation`, `adapters`, and `tasks_by_status`. `project` SHALL contain only `id` and `name`. `columns`, `board_empty_states`, `board_summary.counts`, `automation.counts`, and `tasks_by_status` SHALL use exactly the canonical `Estimated`, `Running`, `Review`, and `Done` keys. `board_summary` SHALL contain only `launch_ready`, `total_tasks`, `counts`, `archived_count`, and `history_total_tasks`. `automation` SHALL contain only `counts`, `eligible_count`, `queue`, and `live_refresh_enabled`; `queue` SHALL contain only `status`, `auto_agent_review`, and `latest_stop_reason`.

Each adapter SHALL contain only `id`, `name`, `is_default`, `launchable`, `allowed_models`, and `tracking`. Each task card SHALL contain only `id`, `status`, `task_kind`, `summary`, `estimate_tokens`, `actual_tokens`, `recommended_model`, `launch_model`, `session_href`, `review_prompt`, `timeline`, `blocked_condition`, and `controls`. `task_kind` SHALL be exactly `implementation`, `scout`, or `acceptance_verification`. `blocked_condition`, when present, SHALL contain only a bounded `reason`, `origin`, and `timestamp`. `review_prompt` SHALL be bounded control state, and `timeline` SHALL contain at most the six newest bounded live-event summaries needed by Running cards. `controls` SHALL contain only launch, refresh, review, archive, dismissal, setup, manual-estimate, budget-override, and native-usage-acknowledgement fields needed by the two surfaces. Full task, launch, token, log, review, alarm, checkpoint, repository, Scout findings, and pending re-estimation evidence SHALL be absent from card payloads and load lazily through `session_href` or bounded Needs You actions into the shared Evidence Drawer or canonical Session Report.

#### Scenario: Board state remains project-scoped
- **WHEN** an authenticated operator requests React project state for `{project_id}`
- **THEN** the response SHALL contain only active tasks bound to `{project_id}`
- **AND** task counts, history link, automation state, launch controls, and Blocked Conditions SHALL refer to that same project

#### Scenario: Board projection allowlists card and adapter fields
- **WHEN** the React project-state endpoint returns task and adapter information
- **THEN** it SHALL include only fields required for Pipeline/Floor rendering, canonical Task kind, action controls, the bounded review prompt, live summaries, Blocked Conditions, and evidence links
- **AND** it SHALL NOT expose adapter configuration, verification payloads, session credentials, raw token-ledger rows, raw Scout findings, pending re-estimation payloads, or unbounded raw task metadata

#### Scenario: Evidence is sanitized and bounded before React receives it
- **WHEN** a task has launch diagnostics, timeline events, logs, Agent Review findings, a Blocked Condition, Scout findings, pending re-estimation evidence, or Worker token components
- **THEN** the React project projection SHALL sanitize secret-bearing operational summaries and bound displayed text
- **AND** timeline entries SHALL include at most the newest six events
- **AND** the response SHALL preserve a session/report link for lazy deeper audit evidence when available

#### Scenario: Card limits and truncation are explicit
- **WHEN** projected card content exceeds its surface-safe limit
- **THEN** summary text SHALL contain at most 400 characters, review-prompt text at most 4,000 characters, timeline summaries at most 1,000 characters, and the timeline SHALL contain at most six items
- **AND** the corresponding required `truncated` boolean SHALL be `true` for affected bounded text
- **AND** secret redaction SHALL occur before truncation

## ADDED Requirements

### Requirement: React workflow exposes Scout kind explicitly
The React project workflow SHALL let operators select Scout for valid short project intake and SHALL render canonical Task kind from bounded backend projections. Direct short intake SHALL default to `implementation` and SHALL offer only `implementation` or `scout`; `acceptance_verification` remains available through Task Breakdown Review.

#### Scenario: Operator creates Scout from short intake
- **WHEN** an operator selects Scout and submits valid short task text from the project Pipeline
- **THEN** React sends `task_kind: scout` through the existing negotiated project intake action
- **AND** FastAPI remains authoritative for validation, estimation, project binding, and the returned Task outcome

#### Scenario: Operator omits kind
- **WHEN** an operator submits short project intake without changing Task kind
- **THEN** React sends or the backend derives `task_kind: implementation`
- **AND** existing implementation intake behavior remains unchanged

#### Scenario: Scout card is explicit
- **WHEN** a bounded Task projection has `task_kind: scout`
- **THEN** React displays a visible Scout label on Pipeline, Floor, history, and linked Needs You surfaces where that Task appears
- **AND** it does not infer the label from task prose or expose raw metadata

### Requirement: React low-confidence actions remain backend-authoritative
The React Needs You surface SHALL display low-confidence estimate evidence and explicit actions supplied by the backend. React SHALL NOT locally acknowledge, replace, create, re-estimate, or apply Task estimates.

#### Scenario: Low-confidence item shows choices
- **WHEN** Needs You returns a low-confidence Task item
- **THEN** React displays its bounded confidence value and actions to acknowledge, enter a manual estimate, or create a linked Scout
- **AND** each action uses an authenticated backend mutation with explicit JSON negotiation
- **AND** successful mutation triggers an authoritative Pipeline/Needs You reload

#### Scenario: Scout findings are ready
- **WHEN** Needs You reports that a linked Scout has completed and its Session Report is available
- **THEN** React links to the canonical Session Report
- **AND** offers the backend-authoritative request-re-estimate action
- **AND** does not apply any pending re-estimate without a separate explicit operator action

#### Scenario: Mutation fails
- **WHEN** a low-confidence, Scout-creation, re-estimation, or Apply action returns a sanitized validation or conflict error
- **THEN** React preserves current authoritative Task data and shows the error
- **AND** it does not assume the requested state change succeeded
