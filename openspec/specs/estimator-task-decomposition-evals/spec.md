# estimator-task-decomposition-evals Specification

## Purpose
Define behavior-level evaluation coverage for synthetic repo-aware markdown tasks, Task Breakdown Review classification, accepted-candidate estimation, and explicit breakdown/manual-recovery reasons.

## Requirements

### Requirement: Estimator evals cover repo-aware markdown tasks
The system SHALL include behavioral evals that feed synthetic repo-aware markdown task descriptions into the Task Breakdown Review and Task Estimation flow and verify that accepted output is usable for launch planning.

#### Scenario: Repo-aware markdown task produces reviewed estimated work
- **WHEN** a synthetic markdown task file describes changes against an example repository using DEMO identifiers and 2099 dates
- **THEN** the system creates a Proposed Task Breakdown review before creating Tasks
- **AND** accepted candidates produce estimated work with token estimates, adapter-compatible routed Worker models when available, and source metadata identifying markdown intake

### Requirement: Estimator evals cover decomposition of long and bullet-point tasks
The system SHALL include behavioral evals and golden decomposition fixtures for longer markdown task descriptions and bullet lists that verify semantic classification into vertical-slice candidates, constraints, verification criteria, non-goals, and rejected-as-task reasons before Task Estimation runs.

#### Scenario: Bullet-point task is reviewed before estimated cards exist
- **WHEN** a markdown task file contains multiple implementation bullets with dependencies or phases
- **THEN** the eval fails if persisted Estimated Task cards are created before breakdown review acceptance
- **AND** accepted candidate work items are estimated from scoped task text rather than the full markdown document

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
