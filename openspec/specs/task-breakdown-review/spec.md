# task-breakdown-review Specification

## Purpose
Define how Proposed Task Breakdown review preserves decomposition intent, global source-contract context, and acceptance-verification work before accepted candidates become estimated AGILE Board Tasks.
## Requirements
### Requirement: Durable task breakdown review records
The system SHALL persist Task Breakdown Agent output as a durable Proposed Task Breakdown review record before creating AGILE Board Tasks from Markdown intake or oversized task intake.

#### Scenario: Markdown intake creates review record before tasks
- **WHEN** the operator submits Markdown upload or Markdown paste that requires Task Breakdown Agent interpretation
- **THEN** the system creates a durable Proposed Task Breakdown review record
- **AND** no AGILE Board Task is created until the operator accepts one or more candidates from that review

#### Scenario: Review record preserves breakdown evidence
- **WHEN** a Proposed Task Breakdown is created
- **THEN** the record preserves source metadata, candidate tasks, rejected/non-task items, constraints, verification criteria, Task Breakdown Model identity, and linked orchestration token/session evidence when available

### Requirement: Breakdown review page
The system SHALL provide a separate review page for Proposed Task Breakdowns rather than representing breakdown review as an AGILE Board column or Task state.

#### Scenario: Markdown intake redirects to review page
- **WHEN** Markdown intake successfully produces a Proposed Task Breakdown
- **THEN** the operator is redirected to a breakdown review page for that review record
- **AND** the AGILE Board remains limited to Task lifecycle columns

#### Scenario: Accepting review creates estimated tasks
- **WHEN** the operator accepts one or more candidate tasks from the breakdown review page
- **THEN** the system immediately sends the accepted candidates to Task Estimation
- **AND** creates Estimated AGILE Board Tasks for successful estimates
- **AND** returns the operator to the AGILE Board

### Requirement: Review shows candidates and non-task classifications
The breakdown review page SHALL show candidate vertical slices and explicitly show rejected or non-task source items with reasons.

#### Scenario: Constraint bullet is not a task
- **WHEN** the source contains a bullet such as “Do not add network dependencies.”
- **THEN** the breakdown review shows it as a constraint or rejected-as-task item with a reason
- **AND** the system does not estimate it as a standalone Task

#### Scenario: Verification bullet is not a task
- **WHEN** the source contains a bullet such as “Run pytest.”
- **THEN** the breakdown review shows it as verification criteria or rejected-as-task item with a reason
- **AND** the system does not estimate it as a standalone Task unless the operator explicitly edits it into an implementation candidate

### Requirement: Practical breakdown review editing
The breakdown review page SHALL support practical editing of accepted work without requiring a full planning editor.

#### Scenario: Operator edits candidates before acceptance
- **WHEN** the operator reviews a Proposed Task Breakdown
- **THEN** the operator can accept or reject candidates
- **AND** edit candidate titles or implementation prompts
- **AND** edit constraints and acceptance criteria text before submitting accepted candidates to Task Estimation

#### Scenario: Hard dependency enforcement is not required
- **WHEN** the Task Breakdown Agent suggests a recommended sequence
- **THEN** the system may preserve the sequence as metadata or creation order
- **AND** the first product slice does not require hard dependency blocking between created Tasks

### Requirement: Breakdown failure recovery
The system SHALL show an explicit breakdown-failed recovery state when the Task Breakdown Agent fails or returns invalid structure.

#### Scenario: Breakdown model unavailable
- **WHEN** the Task Breakdown Agent cannot complete because the model provider is unavailable, misconfigured, over budget, or returns invalid output
- **THEN** the system shows a breakdown-failed review/manual recovery screen
- **AND** offers retry, manual candidate creation, single manual candidate creation, or cancel actions
- **AND** does not silently fall back to deterministic Markdown splitting
- **AND** does not create an oversized Estimated Task from the whole source without operator action

### Requirement: Candidate kind is explicit
The system SHALL classify every Proposed Task Breakdown candidate as either `implementation` or `acceptance_verification`.

#### Scenario: Proposed candidate includes kind
- **WHEN** the Task Breakdown Agent returns a Proposed Task Breakdown with candidate Tasks
- **THEN** each candidate includes a candidate kind
- **AND** the candidate kind is either `implementation` or `acceptance_verification`

#### Scenario: Verification intent does not depend on prose
- **WHEN** a candidate is intended to verify the integrated artifact against the original source contract
- **THEN** the candidate kind is `acceptance_verification`
- **AND** the system does not infer that intent from the candidate title or prompt text alone

#### Scenario: Operator edits candidate kind
- **WHEN** the operator reviews candidate Tasks on the Task Breakdown Review page
- **THEN** the operator can edit candidate kind
- **AND** the only available values are `implementation` and `acceptance_verification`

### Requirement: Global contract summary is preserved
The system SHALL preserve one editable global contract summary for each Proposed Task Breakdown and carry it into accepted implementation Tasks.

#### Scenario: Breakdown includes global contract summary
- **WHEN** the Task Breakdown Agent creates a Proposed Task Breakdown
- **THEN** the breakdown includes a global contract summary describing what the accepted slices must collectively satisfy

#### Scenario: Operator edits global contract summary
- **WHEN** the operator reviews a Proposed Task Breakdown
- **THEN** the review page displays the global contract summary
- **AND** the operator can edit the global contract summary before accepting candidates

#### Scenario: Implementation slices inherit global contract summary
- **WHEN** the operator accepts an `implementation` candidate
- **THEN** the accepted Task sent to Task Estimation includes the global contract summary
- **AND** it includes relevant global or candidate-scoped constraints

#### Scenario: Acceptance Verification carries full source contract
- **WHEN** the operator accepts an `acceptance_verification` candidate
- **THEN** the accepted Task sent to Task Estimation includes the global contract summary
- **AND** it includes the full original source contract needed to verify the combined artifact

### Requirement: Breakdown-created implementation prompts use minimal slice context
The system SHALL shape Worker prompts for accepted implementation candidates from a Proposed Task Breakdown using the smallest honest slice context that preserves the task objective, hard constraints, slice-specific acceptance checks, required verification, and a compact global contract summary. The system SHALL NOT repeat unrelated source prose, sibling task details, stale setup text, or raw evidence into every implementation prompt when a compact reference is sufficient.

#### Scenario: Implementation candidate receives ponytail-shaped prompt
- **WHEN** the operator accepts an `implementation` candidate from a Proposed Task Breakdown
- **THEN** the accepted Task sent to Task Estimation and Worker launch context SHALL include the candidate objective or implementation prompt
- **AND** it SHALL include hard global constraints and relevant candidate-scoped acceptance criteria
- **AND** it SHALL include the editable global contract summary in compact form
- **AND** it SHALL omit unrelated sibling candidate details and unnecessary raw source prose from the implementation prompt

#### Scenario: Required guardrails are preserved
- **WHEN** prompt shaping removes repeated or unrelated prose from an implementation candidate
- **THEN** the prompt SHALL still preserve security constraints, no-secret/no-network constraints, synthetic-data rules, required verification commands, expected final response shape, and any acceptance criteria relevant to that candidate

#### Scenario: Acceptance verification keeps enough source contract
- **WHEN** the operator accepts an `acceptance_verification` candidate
- **THEN** the accepted Task SHALL keep the global contract summary and the full original source contract needed to verify the combined artifact
- **AND** prompt shaping SHALL NOT reduce Acceptance Verification into a narrow implementation-slice prompt

### Requirement: Acceptance Verification is proposed for integrated artifacts
The Task Breakdown Agent SHALL auto-propose an Acceptance Verification candidate for multi-slice breakdowns that produce one integrated artifact.

#### Scenario: Integrated artifact receives final verification candidate
- **WHEN** source work is split into multiple implementation candidates for one integrated artifact such as a CLI, app, API, demo, or report
- **THEN** the Proposed Task Breakdown includes an `acceptance_verification` candidate
- **AND** that candidate is recommended last

#### Scenario: Independent slices may reject final verification
- **WHEN** the Task Breakdown Review page shows an `acceptance_verification` candidate
- **THEN** the operator can reject that candidate before creating board Tasks
- **AND** rejecting it does not prevent accepting other implementation candidates

#### Scenario: Launch order is not hard-blocked
- **WHEN** accepted candidates become Estimated AGILE Board Tasks
- **THEN** Acceptance Verification sequence is preserved as metadata or creation order
- **AND** the first implementation does not require hard dependency blocking between created Tasks

### Requirement: Acceptance Verification is ordinary Worker work
Acceptance Verification SHALL be an ordinary estimated AGILE Board Task rather than a hidden control-plane check.

#### Scenario: Accepted Acceptance Verification becomes estimated Task
- **WHEN** the operator accepts an `acceptance_verification` candidate
- **THEN** the system sends it through Task Estimation
- **AND** creates an Estimated AGILE Board Task when estimation succeeds
- **AND** the Task has its own Token Budget, Worker Run, and Review Disposition lifecycle

#### Scenario: Acceptance Verification verifies instead of rebuilding
- **WHEN** an Acceptance Verification Task is launched
- **THEN** the Worker prompt frames the work as verifying the combined artifact against the original source contract
- **AND** it does not ask the Worker to reimplement the whole source task as one oversized implementation Task

#### Scenario: Executable proof is preferred
- **WHEN** an Acceptance Verification Task runs
- **THEN** it uses the smallest executable proof available, such as tests, CLI smoke checks, API calls, artifact parsing, or invariant scans
- **AND** it produces human-readable findings
- **AND** if no executable proof is available, it labels the result manual verification only and explains the evidence gap

#### Scenario: Failed Acceptance Verification does not auto-create repair Tasks
- **WHEN** Acceptance Verification fails
- **THEN** the Task moves to Blocked with findings
- **AND** the system does not automatically create repair Tasks from failure text

### Requirement: Connected-project breakdown uses Repo Context Brief
The Task Breakdown Agent SHALL receive bounded Repo Context Brief information when creating a Proposed Task Breakdown for connected-project intake with a readable project root.

#### Scenario: Project markdown breakdown includes repo context
- **WHEN** an operator submits Markdown upload or Markdown paste from a connected project board
- **AND** the connected project root can be read
- **THEN** the Task Breakdown Agent request includes bounded repo context with available repo instructions, manifests, likely entry points, detected verification commands, and a repository file sample
- **AND** the original source text remains a separate field from the repo context

#### Scenario: Oversized project task breakdown includes repo context
- **WHEN** an operator submits an oversized task from a connected project board that requires Task Breakdown review
- **AND** the connected project root can be read
- **THEN** the Task Breakdown Agent request includes bounded repo context before proposing implementation and Acceptance Verification candidates

#### Scenario: Global breakdown stays unchanged
- **WHEN** an operator submits Markdown or oversized task intake outside a connected project
- **THEN** the Task Breakdown Agent request does not include project repo context
- **AND** Task Breakdown review proceeds with the existing source text, intake metadata, and structure hints

### Requirement: Breakdown review preserves repo-context evidence
The system SHALL preserve bounded repo-context evidence on Proposed Task Breakdown records when repo context is supplied to the Task Breakdown Agent.

#### Scenario: Review record shows context source summary
- **WHEN** a Proposed Task Breakdown is created with Repo Context Brief input
- **THEN** the review record stores bounded repo-context metadata showing the context source list or summary
- **AND** the stored evidence does not include secret-named files or unredacted secret patterns

#### Scenario: Repo context failure does not block manual recovery
- **WHEN** a connected project root is unavailable, unreadable, or otherwise fails while building repo context for Task Breakdown
- **THEN** the system creates or retries the Proposed Task Breakdown without repo context
- **AND** it does not create AGILE Board Tasks without the normal operator acceptance step

### Requirement: Task Breakdown Agent follows Task Slicing Policy
The Task Breakdown Agent SHALL apply a Harness-owned Task Slicing Policy before returning Proposed Task Breakdown candidates. The policy SHALL prefer the fewest useful independently launchable AGILE Board Tasks that preserve the original source contract, avoid speculative work, and include an executable proof or clearly labeled manual proof gap.

#### Scenario: Policy rejects unnecessary board cards
- **WHEN** source intake contains setup prose, context-only bullets, duplicate work, non-goals, constraints, verification notes, or speculative future-proofing
- **THEN** the Task Breakdown Agent SHALL classify those items as rejected or non-task evidence with reasons
- **AND** it SHALL NOT return them as standalone implementation candidates by default

#### Scenario: Policy rejects horizontal layer slices
- **WHEN** source intake could be split into technical layers such as “models,” “routes,” “UI,” and “tests” that are not independently useful or verifiable
- **THEN** the Task Breakdown Agent SHALL prefer tracer-bullet vertical-slice candidates that cut through the needed product layers
- **AND** each returned candidate SHALL have its own acceptance criteria and proof path

#### Scenario: Policy preserves root-cause/shared-seam work
- **WHEN** multiple requested changes are symptoms of one shared behavior or code seam
- **THEN** the Task Breakdown Agent SHALL prefer one candidate focused on the shared seam over duplicated caller-level candidates
- **AND** the candidate SHALL explain why the shared task is not smaller

### Requirement: Candidates include quality evidence
Every Proposed Task Breakdown candidate SHALL include structured quality evidence that explains why it deserves an AGILE Board Task and how it can be verified.

#### Scenario: Candidate carries slicing evidence
- **WHEN** the Task Breakdown Agent returns a candidate
- **THEN** the candidate SHALL include an objective, proof or verification path, why-this-task-exists rationale, why-not-smaller rationale, and why-not-larger rationale
- **AND** the candidate SHALL include dependencies by candidate title when the slice should run after another accepted candidate

#### Scenario: Candidate uses repo context as hints only
- **WHEN** connected-project Repo Context Brief input is available
- **THEN** candidates MAY include likely repo entry points, test commands, or docs from that brief
- **AND** those entry points SHALL be treated as launch guidance rather than proof of deep source analysis

#### Scenario: Accepted task preserves policy evidence
- **WHEN** an operator accepts a Proposed Task Breakdown candidate
- **THEN** the accepted Task metadata SHALL preserve the candidate quality evidence
- **AND** the Task description sent to Task Estimation SHALL include the execution-relevant objective, scope, acceptance criteria, constraints, dependencies, and verification proof

### Requirement: Candidates classify execution mode
Every Proposed Task Breakdown candidate SHALL classify whether it is autonomous or human-in-the-loop before it becomes an AGILE Board Task.

#### Scenario: AFK candidate is independently executable
- **WHEN** a candidate can be implemented and verified by a Worker without waiting for operator decisions, credentials, external approvals, or manual product judgment during execution
- **THEN** the candidate execution mode SHALL be `AFK`
- **AND** the candidate SHALL include a runnable or inspectable verification proof where feasible

#### Scenario: HITL candidate names human dependency
- **WHEN** a candidate requires operator choice, manual QA, external approval, credentials, deployment permission, or stakeholder review before completion
- **THEN** the candidate execution mode SHALL be `HITL`
- **AND** the candidate SHALL include the reason human input is required

#### Scenario: Execution mode is separate from candidate kind
- **WHEN** a candidate is classified for Task Breakdown Review
- **THEN** `execution_mode` SHALL NOT replace candidate `kind`
- **AND** candidate `kind` SHALL continue to distinguish `implementation` from `acceptance_verification`

### Requirement: Implementation prompts carry smallest honest executable context
Accepted implementation candidates SHALL produce Worker-facing task text that is compact but includes enough execution policy to prevent whole-task reruns, under-scoped work, and unverified changes.

#### Scenario: Implementation task includes proof and boundaries
- **WHEN** an operator accepts an `implementation` candidate
- **THEN** the created Task description SHALL include the candidate objective, implementation prompt, compact global contract summary, relevant constraints, acceptance criteria, dependencies, and verification proof
- **AND** it SHALL instruct the Worker not to re-solve the entire original source task

#### Scenario: Implementation task omits unrelated source prose
- **WHEN** an implementation candidate is accepted from a multi-slice Proposed Task Breakdown
- **THEN** the created Task description SHALL omit unrelated sibling candidate details, raw source prose not needed for that slice, and stale setup text
- **AND** it SHALL preserve hard constraints such as security, no-secret/no-network, synthetic-data, required verification, and expected final response shape when present

#### Scenario: Acceptance Verification keeps original contract
- **WHEN** an `acceptance_verification` candidate is accepted
- **THEN** the created Task description SHALL include the global contract summary and the original source contract needed to verify the combined artifact
- **AND** it SHALL frame the work as verification/proof rather than reimplementation

### Requirement: Breakdown failure diagnostics are safe and actionable
The system SHALL record Task Breakdown Agent failures with safe diagnostics that distinguish provider rejection from large-request timeout behavior while preserving manual recovery.

#### Scenario: Anthropic parameter rejection creates failed review
- **WHEN** the Task Breakdown Agent provider rejects a request with a sanitized HTTP error such as an unsupported parameter error
- **THEN** the Proposed Task Breakdown record SHALL be marked failed with `manual_required` decision
- **AND** the failure message SHALL include the sanitized provider error and model identity when available
- **AND** retry, manual candidate creation, single manual candidate creation, and cancel actions SHALL remain available

#### Scenario: Large Task Breakdown request times out
- **WHEN** the Task Breakdown Agent request times out before a complete provider response is received
- **THEN** the Proposed Task Breakdown record SHALL be marked failed with `manual_required` decision
- **AND** the failure message SHALL include safe diagnostics for model, timeout seconds, source character length, and max output tokens
- **AND** the failure message SHALL NOT include raw source text, prompt text, API keys, or secret values
- **AND** retry, manual candidate creation, single manual candidate creation, and cancel actions SHALL remain available

#### Scenario: Connection test success is not treated as breakdown success
- **WHEN** the Control Plane connection test has recorded success for a model
- **AND** a later Task Breakdown Agent request fails because of provider parameter rejection or timeout
- **THEN** the Task Breakdown review SHALL show the Task Breakdown failure state
- **AND** it SHALL NOT present the prior connection test as proof that the full breakdown request succeeded

