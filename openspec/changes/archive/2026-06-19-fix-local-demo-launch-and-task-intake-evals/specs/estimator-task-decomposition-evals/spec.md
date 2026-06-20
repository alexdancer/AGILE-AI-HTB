## ADDED Requirements

### Requirement: Estimator evals cover repo-aware markdown tasks
The system SHALL include behavioral evals that feed synthetic repo-aware markdown task descriptions into the estimator and verify that the output is usable for launch planning.

#### Scenario: Repo-aware markdown task produces estimated work
- **WHEN** a synthetic markdown task file describes changes against an example repository using DEMO identifiers and 2099 dates
- **THEN** the estimator creates estimated work with token estimates, model recommendations constrained to available Worker models when applicable, and source metadata identifying markdown intake

### Requirement: Estimator evals cover decomposition of long and bullet-point tasks
The system SHALL include behavioral evals for longer markdown task descriptions and bullet lists that verify decomposition into multiple estimated tasks or explicit task breakdown metadata.

#### Scenario: Bullet-point task is separated into work items
- **WHEN** a markdown task file contains multiple implementation bullets with dependencies or phases
- **THEN** the estimator output separates the work into multiple tasks or records structured breakdown metadata
- **AND** each separated work item has an estimate or a clear reason why it requires manual estimation

#### Scenario: Complex markdown produces explicit rejection reasons
- **WHEN** a markdown task cannot be safely estimated or decomposed
- **THEN** the estimator output includes a specific rejection or manual-estimate reason instead of a vague null or uncertain result
