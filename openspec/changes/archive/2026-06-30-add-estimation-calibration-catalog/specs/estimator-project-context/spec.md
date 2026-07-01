## ADDED Requirements

### Requirement: Estimator receives calibration summary when relevant

When estimating a task and relevant calibration cases are available, the estimator SHALL receive a bounded calibration summary alongside the existing task description, budget numbers, and any Repo Context Brief. The calibration summary SHALL be optional and SHALL NOT be required for global or project-scoped estimation to proceed.

#### Scenario: Project estimate includes repo context and calibration summary

- **WHEN** an operator estimates a project-board task and relevant calibration cases are available
- **THEN** the estimator input includes the existing project context brief
- **AND** the estimator input includes a bounded calibration summary

#### Scenario: Project estimate has no relevant calibration cases

- **WHEN** an operator estimates a project-board task and no relevant calibration cases are available
- **THEN** the estimator input includes the existing project context brief
- **AND** no calibration summary is included
- **AND** estimation proceeds normally

#### Scenario: Global estimate can use catalog without project context

- **WHEN** an operator estimates a global-board task and relevant non-project-specific calibration cases are available
- **THEN** the estimator may receive a calibration summary
- **AND** the estimator receives no Repo Context Brief

### Requirement: Calibration summary is auditable context

The calibration summary SHALL identify the selected calibration case IDs and ranges in a readable form suitable for test assertions and debugging. The summary SHALL NOT include full Worker logs, secrets, raw provider usage JSON, or unbounded repo content.

#### Scenario: Summary omits raw evidence

- **WHEN** a selected calibration case has optional actual Worker tokens or rationale
- **THEN** the calibration summary may include the case ID, expected range, optional actual token count, and rationale
- **AND** the summary does not include raw provider usage JSON or full Worker logs
