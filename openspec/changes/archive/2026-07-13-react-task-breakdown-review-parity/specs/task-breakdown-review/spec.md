## MODIFIED Requirements

### Requirement: Breakdown review page
The system SHALL provide a separate canonical review page for Proposed Task Breakdowns rather than representing breakdown review as an AGILE Board column or Task state. When the complete React build is available, `/task-breakdowns/{breakdown_id}/review` SHALL render inside the React Portal shell; when the build is missing or partial, the same canonical URL SHALL preserve the existing Jinja review.

#### Scenario: Markdown intake redirects to review page
- **WHEN** Markdown intake successfully produces a Proposed Task Breakdown
- **THEN** the operator is directed to `/task-breakdowns/{breakdown_id}/review` for that durable review record
- **AND** the AGILE Board remains limited to Task lifecycle columns

#### Scenario: Built canonical review opens in React
- **WHEN** an authenticated operator opens an existing Task Breakdown Review while the complete frontend build is available
- **THEN** FastAPI SHALL return the React shell for the canonical review URL
- **AND** React SHALL render the review inside the shared Portal chrome
- **AND** no `/app/task-breakdowns` alias SHALL be introduced

#### Scenario: Missing or partial build preserves Jinja review
- **WHEN** an authenticated operator opens an existing Task Breakdown Review while the frontend build is missing or partial
- **THEN** FastAPI SHALL render the existing Jinja review at the same canonical URL
- **AND** the operator SHALL retain the complete acceptance and recovery workflow

#### Scenario: Unknown review stays backend-authoritative
- **WHEN** an authenticated operator opens the canonical review URL for an unknown breakdown id
- **THEN** FastAPI SHALL return `404`
- **AND** a complete React build SHALL NOT turn the unknown review into a successful shell-only page

#### Scenario: Accepting review creates estimated tasks
- **WHEN** the operator accepts one or more candidate tasks from the breakdown review page
- **THEN** the system immediately sends the accepted candidates to Task Estimation
- **AND** creates Estimated AGILE Board Tasks for successful estimates
- **AND** returns the operator to the canonical project-scoped or global AGILE Board

### Requirement: Review shows candidates and non-task classifications
The breakdown review page SHALL show candidate vertical slices and explicitly show rejected or non-task source items with reasons. React SHALL preserve all source-contract and classification evidence visible in the Jinja review, while allowing dense slicing and Repo Context evidence to use progressive disclosure.

#### Scenario: Constraint bullet is not a task
- **WHEN** the source contains a bullet such as “Do not add network dependencies.”
- **THEN** the breakdown review shows it as a constraint or rejected-as-task item with a reason
- **AND** the system does not estimate it as a standalone Task

#### Scenario: Verification bullet is not a task
- **WHEN** the source contains a bullet such as “Run pytest.”
- **THEN** the breakdown review shows it as verification criteria or rejected-as-task item with a reason
- **AND** the system does not estimate it as a standalone Task unless the operator explicitly edits it into an implementation candidate

#### Scenario: React preserves secondary review evidence
- **WHEN** rejected items, non-goals, recommended sequence, source/model/session evidence, rationale, or Repo Context evidence exists
- **THEN** React SHALL keep that evidence visible in bounded summary or native disclosure sections
- **AND** the Session link SHALL use the canonical React-owned Session Report route
- **AND** local project root, secret-bearing source metadata, raw provider payloads, and unknown persisted fields SHALL NOT be exposed

### Requirement: Practical breakdown review editing
The breakdown review page SHALL support practical editing of accepted work without requiring a full planning editor. React SHALL keep pre-acceptance changes browser-local and SHALL persist reviewed candidates only through explicit acceptance.

#### Scenario: Operator edits candidates before acceptance
- **WHEN** the operator reviews a Proposed Task Breakdown
- **THEN** the operator can accept or reject candidates
- **AND** edit candidate kind, execution mode, title, objective, implementation prompt, acceptance criteria, proof, HITL reason, task-specific constraints, why-this-task-exists, why-not-smaller, why-not-larger, dependencies, and likely repo entry points
- **AND** edit global contract summary, global constraints, and verification before submitting accepted candidates to Task Estimation

#### Scenario: Dense slicing evidence uses progressive disclosure
- **WHEN** a candidate includes rationale, dependency, or likely-entry-point detail
- **THEN** candidate selection and primary editable fields SHALL remain immediately visible
- **AND** why-this-task-exists, why-not-smaller, why-not-larger, dependencies, and likely entry points MAY use native disclosure without becoming inaccessible

#### Scenario: Bounded editable text is not silently submitted
- **WHEN** an editable field is truncated in the bounded React projection
- **THEN** React SHALL require the generated authenticated full-text load before enabling edits to that field
- **AND** an untouched field SHALL be omitted from the Accept request so the backend preserves the authoritative original value
- **AND** React SHALL NOT submit a preview as the complete candidate field

#### Scenario: Present empty optional values clear intentionally
- **WHEN** an operator intentionally clears candidate constraints, dependencies, likely entry points, optional HITL evidence valid for the selected mode, global constraints, or verification
- **THEN** React SHALL submit that field as present and empty
- **AND** FastAPI SHALL clear the optional/list value rather than replacing it with the persisted original
- **AND** omitted untouched fields SHALL still preserve their persisted originals
- **AND** present empty required candidate fields SHALL return `422`

#### Scenario: Every candidate is loaded before acceptance
- **WHEN** a review has more candidates than the initial bounded page
- **THEN** React SHALL keep final acceptance disabled until all candidate pages are loaded
- **AND** unseen candidates SHALL NOT be silently accepted or discarded

#### Scenario: Unsaved edits are protected
- **WHEN** the operator has changed review fields and attempts ordinary in-shell navigation, browser Back/Forward, Cancel, reload, or tab close
- **THEN** React SHALL warn before discarding the browser-local draft
- **AND** canceling navigation SHALL retain the current URL and edits
- **AND** successful Accept, Retry, or Manual Candidate handling SHALL clear superseded dirty state before authoritative navigation or refetch

#### Scenario: Hard dependency enforcement is not required
- **WHEN** the Task Breakdown Agent suggests a recommended sequence
- **THEN** the system may preserve the sequence as metadata or creation order
- **AND** the first product slice does not require hard dependency blocking between created Tasks

### Requirement: Breakdown failure recovery
The system SHALL show an explicit breakdown-failed recovery state when the Task Breakdown Agent fails or returns invalid structure. React SHALL use the existing Retry and Manual Candidate actions through explicit JSON negotiation while HTML forms retain their existing redirects.

#### Scenario: Breakdown model unavailable
- **WHEN** the Task Breakdown Agent cannot complete because the model provider is unavailable, misconfigured, over budget, or returns invalid output
- **THEN** the system shows a breakdown-failed review/manual recovery screen
- **AND** offers retry, manual candidate creation, single manual candidate creation, or cancel actions
- **AND** does not silently fall back to deterministic Markdown splitting
- **AND** does not create an oversized Estimated Task from the whole source without operator action

#### Scenario: React retries failed breakdown
- **WHEN** an operator activates Retry from a failed React review
- **THEN** React SHALL call the existing Retry path with explicit JSON negotiation
- **AND** a completed retry SHALL refetch and render the authoritative proposed or failed review state
- **AND** it SHALL NOT create AGILE Board Tasks

#### Scenario: React creates manual recovery candidate
- **WHEN** an operator submits a Manual Candidate from a failed React review
- **THEN** React SHALL call the existing Manual Candidate path with explicit JSON negotiation
- **AND** the resulting authoritative proposed review SHALL replace the failed state after a successful refetch
- **AND** no AGILE Board Task SHALL exist until explicit acceptance

#### Scenario: Accepted review cannot be reopened by stale recovery
- **WHEN** Retry or Manual Candidate is submitted for an already accepted review
- **THEN** the operation SHALL be idempotent
- **AND** it SHALL return or redirect to the canonical board without replacing accepted candidates or created Task ids

### Requirement: Breakdown review preserves repo-context evidence
The system SHALL preserve bounded repo-context evidence on Proposed Task Breakdown records when repo context is supplied to the Task Breakdown Agent. The React review SHALL expose the safe context-source summary without revealing local project-root or secret-bearing metadata.

#### Scenario: Review record shows context source summary
- **WHEN** a Proposed Task Breakdown is created with Repo Context Brief input
- **THEN** the review record stores bounded repo-context metadata showing the context source list or summary
- **AND** the stored evidence does not include `.env*`, `credentials.*`, other secret-named files, opaque values under exact generic `token`/credential keys, or unredacted secret patterns

#### Scenario: React review shows safe Repo Context evidence
- **WHEN** a stored review has Repo Context evidence
- **THEN** React SHALL show source, text size, documents, manifests, entry points, test commands, and tracked-file sample through bounded pageable evidence
- **AND** it SHALL exclude project root, raw file contents, secrets, and unknown metadata fields

#### Scenario: Repo context failure does not block manual recovery
- **WHEN** a connected project root is unavailable, unreadable, or otherwise fails while building repo context for Task Breakdown
- **THEN** the system creates or retries the Proposed Task Breakdown without repo context
- **AND** it does not create AGILE Board Tasks without the normal operator acceptance step

## ADDED Requirements

### Requirement: Task Breakdown Review mutations remain backend-authoritative and idempotent
FastAPI SHALL remain the sole domain authority for review status, presence-aware candidate/global edits, candidate validation, Task Estimation, Task creation, project binding, Retry, Manual Candidate recovery, and idempotency. Transport-specific JSON/HTML negotiation SHALL NOT redefine those domain outcomes.

#### Scenario: Valid acceptance materializes tasks once
- **WHEN** an operator accepts one or more valid selected candidates from a proposed review
- **THEN** FastAPI SHALL normalize the presence-aware edits, estimate and create Tasks using the existing acceptance path, persist accepted candidates/global contract/global constraints/verification and created Task ids, and mark the review accepted
- **AND** each accepted candidate SHALL materialize at most once for that durable review

#### Scenario: Concurrent acceptance has one immutable owner
- **WHEN** concurrent Accept requests target the same proposed or pending-review record with identical or conflicting selections and edits
- **THEN** FastAPI SHALL atomically persist one immutable accepted-candidate/global snapshot in an internal `accepting` claim before Task Estimation
- **AND** only the claim owner SHALL call the estimator or materialize Tasks
- **AND** non-owning requests SHALL receive a fixed conflict while the claim is active or the canonical accepted replay after completion
- **AND** every materialized Task id SHALL remain linked in the durable review evidence

#### Scenario: Interrupted acceptance fails closed
- **WHEN** any exception occurs after an acceptance owner has durably claimed the record, including after provider, accounting-session, or partial Task side effects
- **THEN** FastAPI SHALL expose a normalized proposed read-only projection with every mutation control disabled
- **AND** it SHALL retain the immutable claimed candidates, global evidence, and every discoverable materialized Task id
- **AND** it SHALL NOT roll back or time-reclaim the claim or rerun estimation because the estimator/provider has no idempotency contract
- **AND** recovery SHALL require controlled operator repair outside the negotiated Accept, Retry, and Manual Candidate actions

#### Scenario: Stale asynchronous recovery cannot overwrite accepted state
- **WHEN** Retry or Manual Candidate starts before another request claims and accepts the review
- **THEN** its final persistence SHALL fail the expected status/monotonic-revision compare-and-set even when wall-clock timestamps repeat
- **AND** it SHALL return the canonical accepted replay without replacing accepted candidates, evidence, Task ids, or status

#### Scenario: Invalid acceptance leaves the review unaccepted
- **WHEN** no candidate is selected or a selected candidate/global edit fails backend validation
- **THEN** FastAPI SHALL reject acceptance without marking the review accepted
- **AND** it SHALL NOT create Tasks for a handled validation failure
- **AND** the durable proposed/failed review evidence SHALL remain available for correction or recovery

#### Scenario: Failed review cannot be accepted
- **WHEN** Accept targets a review whose status is `failed`
- **THEN** FastAPI SHALL reject acceptance without creating Tasks
- **AND** Retry or Manual Candidate SHALL remain the required recovery path

#### Scenario: Accepted review mutation replay is idempotent
- **WHEN** Accept, Retry, or Manual Candidate targets an already accepted review
- **THEN** FastAPI SHALL retain the existing accepted candidates, global evidence, created Task ids, and accepted status
- **AND** it SHALL NOT duplicate Tasks, rerun Task Breakdown, or reopen the review

#### Scenario: Retry replaces only pre-acceptance review evidence
- **WHEN** Retry completes for a proposed or failed review
- **THEN** FastAPI SHALL persist the authoritative new proposed or failed review result
- **AND** it SHALL NOT create AGILE Board Tasks

#### Scenario: Manual Candidate creates review evidence before Tasks
- **WHEN** Manual Candidate succeeds for a proposed or failed review
- **THEN** FastAPI SHALL persist one proposed manual candidate with the existing manual HITL policy evidence
- **AND** it SHALL NOT create an AGILE Board Task until later explicit acceptance
