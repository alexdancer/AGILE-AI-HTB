# estimation-calibration-catalog Specification

## Purpose
TBD - created by archiving change add-estimation-calibration-catalog. Update Purpose after archive.
## Requirements
### Requirement: Manual calibration catalog schema

The system SHALL support manual estimation calibration cases for Worker execution token estimates. Each valid case SHALL include an identifier, task description, expected Worker-token range, complexity, task kind, recommended Worker model, project profile metadata, and rationale. A case MAY include actual Worker tokens when the value is known.

#### Scenario: Valid structured case

- **WHEN** a calibration catalog contains a case with `id`, `task_description`, `expected_tokens_min`, `expected_tokens_max`, `complexity`, `task_kind`, `recommended_model`, `project_profile`, and `rationale`
- **THEN** the system accepts the case as a calibration candidate
- **AND** the candidate is available for estimator relevance selection

#### Scenario: Case with optional actual tokens

- **WHEN** a valid calibration case includes `actual_tokens`
- **THEN** the system preserves the actual Worker-token value as evidence
- **AND** the value does not replace the expected token range

### Requirement: Catalog sources

The system SHALL support a checked-in sample or default calibration catalog for schema examples and regression tests, and SHALL support a repo-local `.htb/estimation_calibration.yaml` catalog for operator-authored project calibration data.

#### Scenario: Checked-in catalog available

- **WHEN** the checked-in calibration catalog exists
- **THEN** the system can load it for tests, examples, and default calibration cases

#### Scenario: Local operator catalog available

- **WHEN** `.htb/estimation_calibration.yaml` exists for the active repository
- **THEN** the system loads valid local cases as additional calibration candidates
- **AND** the local catalog is treated as operator data rather than committed product defaults

### Requirement: Catalog validation modes

The system SHALL validate checked-in and test calibration catalogs strictly. The system SHALL validate local operator catalogs leniently by ignoring malformed cases and exposing warnings without blocking estimation.

#### Scenario: Checked-in catalog is malformed

- **WHEN** a checked-in or test calibration catalog contains a malformed case
- **THEN** catalog validation fails
- **AND** the test or verification command reports the schema error

#### Scenario: Local catalog has one malformed case

- **WHEN** a local operator catalog contains one malformed case and one valid case
- **THEN** the system ignores the malformed case
- **AND** the valid case remains available for relevance selection
- **AND** a warning identifies the ignored case without exposing secrets

### Requirement: Deterministic relevance selection

The system SHALL select relevant calibration cases using deterministic structured filters and simple lexical ranking. Selection SHALL consider available fields such as project profile, task kind, complexity, recommended model, and task-description token overlap. The selected cases SHALL be capped by count and rendered length.

#### Scenario: Relevant cases are ranked deterministically

- **WHEN** multiple calibration cases are available for a task
- **THEN** the system ranks cases using deterministic filters and lexical overlap
- **AND** repeated selection with the same inputs produces the same ordered case IDs

#### Scenario: Selection is bounded

- **WHEN** many calibration cases match a task
- **THEN** the system includes only the configured top cases
- **AND** the rendered calibration summary stays within the configured character cap

### Requirement: Read-only estimator calibration summary

The system SHALL render selected calibration cases as a bounded read-only summary for Task Estimation. The summary SHALL describe relevant historical or manually authored Worker-token ranges and rationale, but SHALL NOT directly multiply, clamp, or overwrite the estimator's returned token estimate.

#### Scenario: Calibration summary is included for relevant cases

- **WHEN** relevant calibration cases exist for an estimated task
- **THEN** the estimator receives a calibration summary containing selected case IDs, expected Worker-token ranges, optional actual Worker tokens, and rationales
- **AND** the estimator still returns the final structured estimate JSON

#### Scenario: No relevant cases exist

- **WHEN** no calibration cases match the task
- **THEN** Task Estimation proceeds without a calibration summary
- **AND** existing no-calibration behavior is preserved

### Requirement: SQL calibration seam

The calibration system SHALL preserve a seam for future SQL-derived completed-task calibration candidates without requiring SQL history as the first source of truth.

#### Scenario: Manual catalog remains primary in first slice

- **WHEN** the first calibration implementation is enabled
- **THEN** manually loaded catalog cases provide the calibration summary source
- **AND** completed-task SQL history is not required for estimation to proceed

