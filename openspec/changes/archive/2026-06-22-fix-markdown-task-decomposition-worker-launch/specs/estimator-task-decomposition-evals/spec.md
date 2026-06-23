## MODIFIED Requirements

### Requirement: Estimator evals cover decomposition of long and bullet-point tasks
The system SHALL include behavioral evals for longer markdown task descriptions and bullet lists that verify decomposition into multiple persisted estimated tasks when deterministic task items are present, or explicit task breakdown/manual-estimate metadata when decomposition is not safe.

#### Scenario: Bullet-point task is separated into work items
- **WHEN** a markdown task file contains multiple implementation bullets with dependencies or phases
- **THEN** the estimator output creates multiple persisted task cards or records a specific reason why card-level decomposition requires manual estimation
- **AND** each separated work item has an estimate or a clear reason why it requires manual estimation
- **AND** each separated work item is estimated from scoped task text rather than the full markdown document

#### Scenario: Complex markdown produces explicit rejection reasons
- **WHEN** a markdown task cannot be safely estimated or decomposed
- **THEN** the estimator output includes a specific rejection or manual-estimate reason instead of a vague null or uncertain result

#### Scenario: Markdown import regression detects one-card collapse
- **WHEN** a synthetic `.md` file contains three checklist tasks with DEMO identifiers
- **THEN** the regression eval fails if only one persisted task card is created
- **AND** the eval fails if any generated card description contains the full original markdown body instead of scoped task content
