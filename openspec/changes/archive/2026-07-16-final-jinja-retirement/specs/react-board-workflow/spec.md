## MODIFIED Requirements

### Requirement: React project board provides the normal governed task loop
The React project board at the canonical `/projects/{project_id}/board` SHALL let an authenticated operator perform the existing normal project-scoped workflow: submit task intake, receive estimated work or an authoritative Task Breakdown Review handoff, launch an Estimated task, refresh Running work, use Review Disposition, and archive or dismiss cards. FastAPI SHALL remain authoritative for every lifecycle transition, project-binding check, estimation, launch guardrail, Worker Run, queue, review, and archive decision.

#### Scenario: React intake creates an estimated project task
- **WHEN** an operator submits a valid short task from the React project board
- **THEN** the system SHALL use the existing project-scoped intake and estimation behavior
- **AND** the React board SHALL reload authoritative board state showing the resulting task outcome

#### Scenario: React markdown intake always requires existing Task Breakdown Review
- **WHEN** an operator submits Markdown text or an uploaded Markdown file from the React project board
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

#### Scenario: React card actions preserve backend workflow authority
- **WHEN** an operator launches, refreshes, saves a review prompt, requests Agent Review, marks Done, blocks, archives, dismisses, runs next, starts/stops a queue, or archives Done cards from the React board
- **THEN** the system SHALL execute the existing authoritative FastAPI action behavior
- **AND** the React client SHALL NOT directly mutate lifecycle, budget, queue, token, or review state

### Requirement: React board action responses support in-shell workflow
Existing authenticated board action paths used by the React board SHALL preserve their existing redirect behavior for non-JSON callers and SHALL provide negotiated JSON outcomes for explicit React callers. JSON outcomes SHALL identify success or a sanitized validation/guardrail failure and SHALL provide an explicit next URL when the existing workflow directs the operator to another canonical route.

#### Scenario: Non-JSON callers keep the existing redirect behavior
- **WHEN** a non-JSON caller submits an existing intake, launch, refresh, queue, review, archive, or dismiss action
- **THEN** the system SHALL preserve its existing redirect/error behavior
- **AND** the redirect target SHALL remain the canonical route it names, which the React shell then renders
- **AND** the change SHALL NOT require those callers to use JSON

#### Scenario: Explicit JSON negotiation returns a stable outcome
- **WHEN** a React caller submits JSON or multipart board data with `Accept: application/json`
- **THEN** the action SHALL return `application/json` rather than a redirect
- **AND** the response SHALL include `ok`, `error`, `setup_href`, and `next_href` fields, with unavailable values represented as `null`
- **AND** successful in-board outcomes SHALL include an authoritative task or automation result when that action creates or changes one

#### Scenario: No JSON negotiation preserves browser behavior
- **WHEN** an existing board action request does not explicitly accept `application/json`
- **THEN** the action SHALL retain its established HTML redirect or error representation
- **AND** multipart Markdown intake SHALL follow the same negotiation rule

#### Scenario: React action stays in board after outcome
- **WHEN** a React board action completes with an in-board outcome
- **THEN** the client SHALL receive a structured JSON result
- **AND** the client SHALL reload bounded authoritative project-board state instead of performing a full-page navigation

#### Scenario: React action reports authoritative guardrail failure
- **WHEN** a React launch or automation action is rejected by existing project, adapter, allowed-model, budget, native-usage acknowledgement, or lifecycle guardrails
- **THEN** the response SHALL expose only sanitized actionable failure information
- **AND** the React board SHALL retain the task's backend-authoritative state and relevant setup link when one exists
