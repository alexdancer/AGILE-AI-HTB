## MODIFIED Requirements

### Requirement: Estimator evals cover decomposition of long and bullet-point tasks
The system SHALL include behavioral evals and golden decomposition fixtures for longer markdown task descriptions and bullet lists that verify semantic classification into vertical-slice candidates, constraints, verification criteria, non-goals, and rejected-as-task reasons before Task Estimation runs. Under the driver-based estimation contract, the estimation-side fixtures SHALL assert the emitted Estimation Drivers and the harness-computed `token_estimate` (with its coefficient provenance and persisted shadow/disagreement) rather than a raw LLM-owned token integer.

#### Scenario: Bullet-point task is reviewed before estimated cards exist
- **WHEN** a markdown task file contains multiple implementation bullets with dependencies or phases
- **THEN** the eval fails if persisted Estimated Task cards are created before breakdown review acceptance
- **AND** accepted candidate work items are estimated from scoped task text rather than the full markdown document

#### Scenario: Accepted candidate estimate is driver-computed
- **WHEN** an accepted candidate work item is estimated under the driver-based contract
- **THEN** the eval SHALL assert the estimator emitted Estimation Drivers and a `shadow_token_estimate`
- **AND** the eval SHALL assert the stored `token_estimate` equals the arithmetic computed from those drivers and the resolved adapter/model coefficients
- **AND** the eval SHALL fail if the stored estimate is taken directly from the LLM's owned integer

#### Scenario: Constraint and verification bullets are rejected as tasks
- **WHEN** a markdown fixture contains implementation bullets plus “Do not add network dependencies.” and “Run pytest.”
- **THEN** the golden decomposition output classifies implementation bullets as candidate vertical slices
- **AND** classifies “Do not add network dependencies.” as a constraint or rejected-as-task item with reason `constraint`
- **AND** classifies “Run pytest.” as verification criteria or rejected-as-task item with reason `verification`
- **AND** neither item becomes a standalone Estimated Task unless the operator explicitly edits it into a candidate

#### Scenario: Complex markdown produces explicit rejection reasons
- **WHEN** a markdown task cannot be safely decomposed or estimated
- **THEN** the output includes a specific breakdown failure, rejected-as-task reason, or manual recovery reason instead of a vague null or uncertain result

#### Scenario: Markdown import regression detects deterministic splitting
- **WHEN** a synthetic `.md` file contains three checklist entries with DEMO identifiers plus constraints or verification notes
- **THEN** the regression eval fails if the system creates one persisted task card per raw checklist entry before review acceptance
- **AND** the eval fails if any accepted generated card description contains the full original markdown body instead of scoped candidate content and inherited relevant constraints
