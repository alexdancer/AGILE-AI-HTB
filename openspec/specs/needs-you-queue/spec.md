# needs-you-queue Specification

## Purpose
TBD - created by archiving change two-surface-orchestration-board. Update Purpose after archive.
## Requirements
### Requirement: Needs You aggregates project decisions awaiting a human
The system SHALL provide a project-scoped Needs You queue that aggregates every item awaiting a human decision for the selected project: pending Proposed Task Breakdowns awaiting review, tasks flagged for a manual estimate, launches refused by Launch Guardrails, completed Worker Runs awaiting Review Disposition, budget overrides awaiting approval, and unresolved automatic estimates with confidence below `0.60`. Needs You SHALL be a derived read-model over existing data and SHALL NOT introduce a new persisted lifecycle state. An unresolved low-confidence estimate SHALL be labeled advisory and SHALL NOT itself change Task lifecycle or launch eligibility.

#### Scenario: Needs You lists decisions with reason and action
- **WHEN** an authenticated operator loads Needs You for a project with a pending breakdown and a task flagged for manual estimate
- **THEN** each entry SHALL name its reason and the action that clears it
- **AND** entries SHALL be scoped to the selected project

#### Scenario: Empty Needs You renders a bounded empty state
- **WHEN** an authenticated operator loads Needs You for a project with no pending decisions
- **THEN** the surface SHALL render a concise empty state rather than an error or a fabricated item

#### Scenario: Advisory low-confidence item appears without blocking launch
- **WHEN** a project Task has an unresolved automatic estimate with confidence below `0.60`
- **THEN** Needs You includes a `low_confidence_estimate` decision for that Task
- **AND** the item identifies the decision as advisory
- **AND** launch remains available when all ordinary Launch Guardrails pass

### Requirement: Needs You is pinned on the Pipeline Surface with a navigation badge
The Needs You queue SHALL appear as a section pinned at the top of the Pipeline Surface, and project navigation SHALL show a live count badge so the queue stays reachable from the Execution Floor.

#### Scenario: Pipeline shows Needs You first
- **WHEN** an authenticated operator opens the Pipeline Surface with one or more pending decisions
- **THEN** Needs You SHALL render above task intake
- **AND** navigation SHALL show a count badge matching the number of pending decisions

#### Scenario: Badge reachable from the Floor
- **WHEN** an authenticated operator is on the Execution Floor with pending decisions
- **THEN** navigation SHALL show the Needs You count badge linking back to the Pipeline Surface Needs You section

### Requirement: Needs You is distinct from Alarms
Needs You SHALL represent operator decisions requiring attention; some decisions block forward progress, while an unresolved low-confidence estimate is explicitly advisory. Needs You SHALL remain separate from Alarms, which represent runtime behavioral warnings about an already-running Worker. The system SHALL NOT merge the two surfaces or convert low confidence into an Alarm or Launch Guardrail failure.

#### Scenario: Runtime alarm does not appear in Needs You
- **WHEN** a running Worker triggers a budget-burn or loop Alarm
- **THEN** that Alarm SHALL appear in the Alarms surface
- **AND** it SHALL NOT be listed as a Needs You decision item

#### Scenario: Advisory estimate decision remains distinct
- **WHEN** a low-confidence estimate appears in Needs You
- **THEN** it is not represented as an Alarm
- **AND** confidence alone does not block launch or forward progress

### Requirement: Low-confidence Needs You projection is exact and bounded
A `low_confidence_estimate` item SHALL contain only `id`, `kind`, `title`, `reason`, `created_at`, `task_id`, `task_kind`, `advisory`, `confidence`, `decision_state`, `scout_task_id`, `session_href`, and `actions`. String ids SHALL contain at most 200 characters, title at most 200, and reason at most 1,000; `created_at` SHALL be a string of at most 64 characters or `null`. `advisory` SHALL be `true`; `confidence` SHALL be a finite number from `0` inclusive to `0.60` exclusive; `task_kind` SHALL use the canonical Task-kind reader. Optional `scout_task_id` and `session_href` SHALL be strings or `null`.

`decision_state` SHALL be exactly `decision_required`, `scout_pending`, `scout_unavailable`, `findings_ready`, `reestimate_running`, `reestimate_ready`, or `reestimate_failed`. `actions` SHALL contain at most three objects, each containing only `kind`, `label`, `method`, and `href`; label SHALL contain at most 80 characters, method SHALL be `GET` or `POST`, and href SHALL contain at most 1,000 characters. Action kind SHALL be one of `acknowledge_estimate`, `manual_estimate`, `create_scout`, `view_scout`, `view_scout_report`, `request_reestimate`, `retry_reestimate`, `apply_reestimate`, or `dismiss_reestimate`. Every href SHALL be generated server-side from the same authenticated project/task/Scout ids, pass the existing safe-local-href policy, and never come from raw metadata. POST hrefs SHALL carry the current expected estimate revision as a generated query value; pending-result Apply/dismiss hrefs SHALL also carry the attempt id. The backend SHALL reject stale query bindings before mutation or external spend.

#### Scenario: Decision-required item exposes exact actions
- **WHEN** a non-Scout low-confidence decision has no linked Scout
- **THEN** `decision_state` is `decision_required`
- **AND** actions are acknowledge estimate, manual estimate, and create Scout in that order
- **AND** a low-confidence Scout omits create Scout and exposes only acknowledgement and manual estimate

#### Scenario: Linked Scout state selects actions
- **WHEN** the linked Scout is pending estimation, awaiting explicit estimation-failure recovery, Estimated, or Running
- **THEN** `decision_state` is `scout_pending` and the only action is `view_scout`
- **AND** initial estimation failure recovery remains visible on the Scout's own Needs You/card evidence rather than creating another Scout
- **WHEN** the linked Scout has a completed Worker Run and usable findings
- **THEN** `decision_state` is `findings_ready` and actions are `view_scout_report` and `request_reestimate`

#### Scenario: Pending re-estimate selects actions
- **WHEN** re-estimation is in progress
- **THEN** `decision_state` is `reestimate_running` and the only action is `view_scout_report`
- **WHEN** a pending result is ready
- **THEN** `decision_state` is `reestimate_ready` and actions are `view_scout_report`, `apply_reestimate`, and `dismiss_reestimate`
- **WHEN** the most recent attempt failed or requires process-crash recovery
- **THEN** `decision_state` is `reestimate_failed` and actions are `view_scout_report`, `retry_reestimate`, and `dismiss_reestimate`

#### Scenario: Malformed projection source fails closed
- **WHEN** confidence is absent, boolean, non-finite, outside the low-confidence range, or otherwise malformed
- **THEN** the backend does not emit a `low_confidence_estimate` item from that value
- **AND** unknown metadata keys and actions are excluded
- **WHEN** a recorded Scout link is missing or does not resolve within the same project
- **THEN** `decision_state` is `scout_unavailable`, optional Scout/report fields are `null`, and only acknowledgement and manual-estimate recovery actions are exposed

### Requirement: Low-confidence and Scout mutations use explicit negotiated outcomes
The authenticated estimate-decision actions SHALL use project/task-scoped POST routes and return JSON to React callers. A success response SHALL contain only `ok`, `project_id`, `task_id`, `decision_state`, `scout_task_id`, and `next_href`; `ok` SHALL be `true`, ids SHALL be strings of at most 200 characters, `scout_task_id` SHALL be a string or `null`, and `next_href` SHALL be a generated safe local project, Scout, or Session Report URL. The response SHALL NOT include raw Task metadata, raw model output, command plans, or secrets.

The POST contracts SHALL be exact: acknowledgement at `/api/projects/{project_id}/tasks/{task_id}/estimate-decision/acknowledge`, manual estimate at `/manual`, Create Scout at `/scout`, request re-estimate at `/scout/reestimate`, explicit recovery retry at `/scout/reestimate/retry`, Apply at `/scout/reestimate/apply`, and dismiss at `/scout/reestimate/dismiss`. The route suffixes are relative to the same estimate-decision base. Acknowledgement, Create Scout, request, Apply, and dismiss accept an empty JSON object only; manual accepts only `estimate_tokens` as a positive integer not greater than `10^15`; recovery retry accepts only `acknowledge_possible_duplicate_spend: true`. React callers SHALL send `Content-Type: application/json` and request JSON. The success-envelope `decision_state` SHALL be one of the item states or `resolved`. A `404`, `422`, or `503` response SHALL contain only `detail` as a sanitized string of at most 1,000 characters. A `409` response SHALL contain only bounded `detail` and the current allowed `decision_state`.

#### Scenario: Mutation succeeds
- **WHEN** acknowledgement, manual estimate, Create Scout, request re-estimate, Apply, or dismiss succeeds
- **THEN** the backend returns `200` with the exact success envelope and resulting decision state
- **AND** an idempotent Create Scout replay returns the existing linked Scout in the same envelope

#### Scenario: Mutation input is invalid
- **WHEN** a request body is malformed, a manual estimate is not a positive bounded integer, or an action is ineligible for canonical Task kind
- **THEN** the backend returns `422` with a sanitized bounded `detail`
- **AND** no partial metadata, Task, estimate, or external model action occurs

#### Scenario: Mutation resource is unavailable
- **WHEN** the project, target Task, linked Scout, completed Worker Run, or Session Report does not exist in the authenticated project scope
- **THEN** the backend returns `404` with sanitized bounded `detail`
- **AND** it does not disclose another project's identifiers or evidence

#### Scenario: Mutation conflicts with authoritative state
- **WHEN** a re-estimation is already running/ready, Apply has a stale estimate revision or disallowed route, or another non-idempotent state precondition fails
- **THEN** the backend returns `409` with sanitized bounded `detail` and an exact current `decision_state`
- **AND** no second external model call or partial canonical update occurs

#### Scenario: Control-plane re-estimation is unavailable
- **WHEN** an eligible synchronous re-estimation attempt fails because the configured control-plane model is unavailable
- **THEN** the backend records bounded failed-attempt evidence and returns `503` with sanitized bounded `detail`
- **AND** it preserves the canonical estimate and exposes explicit retry recovery rather than retrying automatically
