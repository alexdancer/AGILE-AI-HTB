## ADDED Requirements

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
