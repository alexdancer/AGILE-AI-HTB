## ADDED Requirements

### Requirement: Scout is a canonical Task kind
The system SHALL represent Task kind as explicit canonical metadata with exactly `implementation`, `scout`, or `acceptance_verification`. When canonical metadata is absent, the system SHALL preserve a valid legacy `task_breakdown_kind`; only Tasks with neither valid form SHALL be treated as `implementation`.

#### Scenario: Legacy breakdown task preserves kind
- **WHEN** the system reads a Task without `task_kind` whose legacy `task_breakdown_kind` is `implementation` or `acceptance_verification`
- **THEN** it uses that valid legacy value as canonical Task kind
- **AND** an existing Acceptance Verification Task is not reclassified as implementation

#### Scenario: Existing task has no valid kind
- **WHEN** the system reads a Task created before canonical Task-kind support without a valid canonical or legacy kind
- **THEN** it treats the Task as `implementation`
- **AND** it does not require a destructive data migration

#### Scenario: Short intake creates Scout
- **WHEN** an operator submits valid short project intake with Task kind `scout`
- **THEN** the system creates and estimates a project-bound Scout Task
- **AND** the stored Task metadata contains `task_kind: scout`

#### Scenario: Invalid task kind is rejected
- **WHEN** Task intake or a mutation supplies a kind outside `implementation`, `scout`, and `acceptance_verification`
- **THEN** the backend rejects the value before creating or changing a Task

### Requirement: Scout uses ordinary governed Task lifecycle
A Scout SHALL be estimated, routed, budgeted, launched through a verified Worker Adapter, accounted, and reviewed through the ordinary Task and Worker Run lifecycle. Scout estimation SHALL preserve a nonzero computed Worker-token estimate and SHALL treat expected repository modifications as zero.

#### Scenario: Scout estimate succeeds
- **WHEN** the control-plane Estimator returns valid Estimation Drivers for a Scout
- **THEN** the Harness computes and stores a nonzero Scout estimate through the existing driver arithmetic
- **AND** the persisted estimate identifies the Task as `scout`
- **AND** Scout estimation does not claim that repository files will be modified

#### Scenario: Scout Worker Run completes
- **WHEN** a Scout passes Launch Guardrails and its Worker Run completes with authoritative usage evidence
- **THEN** the Scout moves to Review through the ordinary Worker lifecycle
- **AND** its normalized Worker usage is stored as the Scout Task's actuals
- **AND** the Scout does not create or use a hidden Spike session

### Requirement: Scout produces a Session Report
A Scout SHALL use the existing Session Report as its findings artifact. Its Worker prompt SHALL request bounded findings, risks, and a recommendation and SHALL prohibit file changes, destructive commands, migrations, and commits.

#### Scenario: Operator reviews Scout findings
- **WHEN** a Scout Worker Run completes successfully
- **THEN** the Scout card and Needs You workflow link to the canonical Session Report
- **AND** the report preserves Worker Run, usage, command, timeline, and repository evidence under existing sanitization and bounded-display rules
- **AND** no Scout-specific report table or artifact format is required

### Requirement: Low estimator confidence creates advisory Needs You work
An automatically estimated Task with confidence below `0.60` SHALL produce a project-scoped Needs You item without changing the Task lifecycle state or blocking launch solely because of confidence. The item SHALL offer backend-authoritative actions to acknowledge the current estimate, enter a manual estimate, or create a linked Scout.

#### Scenario: Confidence below threshold
- **WHEN** a non-Scout Task receives an automatic estimate with confidence less than `0.60`
- **THEN** the Task remains in its existing Estimated lifecycle state
- **AND** Needs You shows the confidence and actions to acknowledge, estimate manually, or create a Scout
- **AND** launch remains available when all ordinary Launch Guardrails pass

#### Scenario: Confidence equals threshold
- **WHEN** an automatic estimate has confidence equal to `0.60`
- **THEN** low-confidence Needs You work is not created

#### Scenario: Operator accepts current estimate
- **WHEN** the operator acknowledges the low-confidence estimate
- **THEN** the backend records the decision durably
- **AND** the low-confidence Needs You item is removed
- **AND** the estimate value remains unchanged

#### Scenario: Operator enters manual estimate
- **WHEN** the operator replaces the low-confidence estimate manually
- **THEN** the Task stores the manual estimate and manual provenance
- **AND** the low-confidence Needs You item is resolved

#### Scenario: Low-confidence Scout cannot create another Scout
- **WHEN** a Scout's own automatic estimate has confidence below `0.60`
- **THEN** Needs You may offer acknowledgement or manual estimation
- **AND** it SHALL NOT offer creation of a nested Scout

### Requirement: Linked Scout does not mutate target estimate
The system SHALL link a low-confidence target Task and exactly one visible Scout for the target's current estimate revision using Task metadata while keeping both as ordinary Tasks. Creating or running the Scout SHALL NOT change the target Task's estimate, routed model, or lifecycle state. Link creation SHALL use an atomic database ownership boundary before control-plane estimation so concurrent or replayed actions cannot create duplicate Scout Tasks or duplicate initial estimation spend for that revision. A later low-confidence estimate revision MAY link a new Scout while prior Scouts retain audit provenance.

#### Scenario: Operator creates Scout from Needs You
- **WHEN** the operator chooses Create Scout for a low-confidence Task
- **THEN** the backend atomically creates one revision-bound project Scout with pending estimation before invoking ordinary Task Estimation
- **AND** the Scout records the target Task id
- **AND** the target records the linked Scout id and waiting decision state
- **AND** no Worker process starts until the operator separately launches the estimated Scout

#### Scenario: Concurrent Create Scout actions
- **WHEN** two authenticated Create Scout actions race for the same target Task
- **THEN** one short database transaction creates and links the Scout to the current estimate revision before any Estimator call
- **AND** the other action returns the same linked Scout as an idempotent success
- **AND** only the creator invokes the control-plane Estimator

#### Scenario: Initial Scout estimation fails
- **WHEN** the control-plane Estimator fails after the Scout link commits
- **THEN** the same visible Scout preserves bounded failure and manual-recovery evidence
- **AND** the target keeps that Scout link
- **AND** retry does not create a second Scout Task

#### Scenario: Linked Scout is still running
- **WHEN** the linked Scout is Estimated or Running
- **THEN** the target Task retains its current estimate and lifecycle
- **AND** the target's Needs You state indicates that Scout findings are pending rather than offering an automatic rewrite

### Requirement: Scout-informed re-estimation is explicit
The system SHALL allow an operator to request a control-plane re-estimate for a target Task only after its linked Scout has a completed Worker Run and canonical Session Report. The request SHALL use a sanitized bounded findings excerpt and SHALL persist the result as a pending re-estimate without changing the canonical estimate until a separate operator Apply action succeeds. Canonical estimate/routing changes SHALL increment a metadata estimate revision used for compare-and-set safety.

#### Scenario: Operator requests re-estimation from completed Scout
- **WHEN** a linked Scout is in Review or Done with a completed Worker Run and Session Report
- **AND** the operator requests re-estimation
- **THEN** the control-plane Estimator receives the target Task context plus a sanitized bounded Scout findings excerpt
- **AND** raw command plans, unbounded logs, local paths, secrets, and unknown metadata are excluded
- **AND** the resulting drivers, computed estimate, confidence, routing evidence, rationale, and Scout provenance are stored as pending evidence
- **AND** the target's current estimate remains unchanged

#### Scenario: Findings excerpt is allowlisted and bounded
- **WHEN** the system builds Scout context for re-estimation
- **THEN** the excerpt contains only `scout_task_id`, `session_id`, `worker_run_id`, `findings`, and `truncated`
- **AND** ids contain at most 200 characters
- **AND** `findings` contains at most six chronological `detail.text` strings from `agent_message` events belonging to the linked Scout's latest completed Worker Run
- **AND** each finding contains at most 2,000 characters and the encoded findings aggregate contains at most 12,000 characters
- **AND** canonical evidence redaction plus project/home-path replacement occurs before truncation
- **AND** `truncated` is true when an eligible item or collection exceeded a bound

#### Scenario: Findings source is malformed or empty
- **WHEN** Worker Run events are not a list, event/detail objects are malformed, eligible text is not a string, or no eligible `agent_message` text remains after redaction
- **THEN** other event kinds, layers, stderr, tool calls, token events, command plans, and unknown fields are ignored
- **AND** re-estimation is unavailable instead of sending guessed, malformed, or raw evidence

#### Scenario: Concurrent re-estimation request
- **WHEN** a pending re-estimation attempt is already `running` or `ready`
- **AND** another request arrives for the same target
- **THEN** the backend returns conflict before invoking the control-plane Estimator again
- **AND** preserves the existing attempt and canonical estimate

#### Scenario: Re-estimation process is interrupted
- **WHEN** a process interruption leaves a `running` attempt without a result
- **THEN** the system does not silently retry
- **AND** recovery requires explicit operator acknowledgement
- **AND** preserves the abandoned attempt and warns that a retry may incur duplicate control-plane spend

#### Scenario: Operator applies pending re-estimate
- **WHEN** a pending Scout-informed re-estimate exists
- **AND** the target estimate revision still matches the revision on which the pending result was based
- **AND** the pending routed model remains allowed for its selected or default Worker Adapter
- **AND** the operator explicitly applies it
- **THEN** the backend atomically updates the canonical estimate and routing fields and increments estimate revision
- **AND** records operator application and Scout provenance for audit

#### Scenario: Target estimate changed before apply
- **WHEN** the target estimate revision no longer matches the revision on which the pending re-estimate was based
- **AND** the operator attempts to apply the pending result
- **THEN** the backend rejects the stale apply
- **AND** it preserves the current canonical estimate

#### Scenario: Pending route is no longer allowed
- **WHEN** the recommended Worker model or adapter in a pending re-estimate is no longer allowed at Apply time
- **THEN** the backend rejects Apply without partially changing canonical estimate or routing fields
- **AND** preserves the pending result for operator review or dismissal

#### Scenario: Operator dismisses pending re-estimate
- **WHEN** the operator dismisses or rejects a pending Scout-informed re-estimate
- **THEN** the target's canonical estimate and routed model remain unchanged
- **AND** the decision remains auditable

### Requirement: Scout accounting and calibration remain isolated
Scout execution usage SHALL be recorded as Worker spend on the Scout Task and SHALL NOT be classified as orchestration spend, included in implementation accuracy aggregates, or used to fit implementation estimation coefficients. Estimation calibration selection SHALL receive canonical Task kind.

#### Scenario: Scout usage is recorded
- **WHEN** a Scout Worker Run emits authoritative usage evidence
- **THEN** normalized usage is attached to the Scout Task's actuals
- **AND** it is included in ordinary Worker budget accounting
- **AND** it is not labeled as task-breakdown, estimation, planning, reporting, or Spike orchestration usage

#### Scenario: Implementation coefficients select fitting evidence
- **WHEN** implementation coefficient fitting selects completed Task evidence
- **THEN** only trustworthy completed evidence with `task_kind: implementation` is eligible
- **AND** Scout actuals are excluded even when their adapter and model match

#### Scenario: Calibration examples are selected by kind
- **WHEN** Task Estimation selects manual calibration examples
- **THEN** it supplies canonical Task kind to deterministic calibration selection
- **AND** Scout and implementation examples do not cross-calibrate solely because their text overlaps

#### Scenario: Implementation accuracy aggregates are computed
- **WHEN** dashboard estimation accuracy selects completed Task evidence
- **THEN** only eligible `implementation` Tasks contribute to the existing aggregate
- **AND** Scout estimate and actual evidence remains visible on the Scout but does not change the implementation calibration indicator
