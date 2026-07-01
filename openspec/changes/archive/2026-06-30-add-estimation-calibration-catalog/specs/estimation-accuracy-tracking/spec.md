## ADDED Requirements

### Requirement: Catalog-backed estimate band evals

The system SHALL include regression coverage that evaluates Task Estimation against calibration catalog cases using Worker execution token estimate bands. The evals SHALL verify that estimator outputs remain within expected ranges for representative cases or produce actionable failure output when they do not.

#### Scenario: Estimate falls inside catalog band

- **WHEN** an estimator eval runs against a calibration case with expected Worker-token minimum and maximum values
- **THEN** the produced `estimate_tokens` value is checked against that expected band
- **AND** the eval records the case ID and estimate result

#### Scenario: Estimate falls outside catalog band

- **WHEN** an estimator eval produces `estimate_tokens` outside the expected band for a calibration case
- **THEN** the eval fails with the case ID, expected range, actual estimate, and task summary

### Requirement: Accuracy scope remains Worker execution tokens

Calibration catalog evals SHALL measure Worker execution token estimates only. They SHALL NOT merge task breakdown, estimation, Agent Review, reporting, adapter verification, or other Control Plane spend into task estimate accuracy.

#### Scenario: Control-plane tokens excluded from calibration eval

- **WHEN** a calibration case or completed task includes Control Plane orchestration usage evidence
- **THEN** the estimate-band eval compares only the task's Worker execution estimate and Worker execution actual or expected range
- **AND** control-plane usage remains separate from the estimate accuracy assertion

### Requirement: Dashboard accuracy metrics remain completed-task based

The existing dashboard estimation accuracy metrics SHALL continue to be computed from completed Done tasks with both estimate and actual Worker tokens. Manual calibration cases SHALL NOT be counted as completed-task dashboard accuracy unless they correspond to persisted Done tasks with actual Worker tokens.

#### Scenario: Manual case does not inflate completed count

- **WHEN** the calibration catalog contains valid manual cases but no Done tasks with actual Worker tokens exist
- **THEN** dashboard `completed_count` remains based on task records only
- **AND** manual catalog cases do not inflate completed-task accuracy metrics
