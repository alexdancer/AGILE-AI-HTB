## ADDED Requirements

### Requirement: Launch controls preserve model-layer clarity
Board launch controls SHALL keep Worker Adapter selection, Worker model selection, and estimator recommendation provenance visually distinct.

#### Scenario: Launch model differs from recommendation
- **WHEN** a task has a recommended model and a different selected or launched Worker model
- **THEN** the board SHALL display the selected/launched Worker model as the primary run model
- **AND** it SHALL keep the estimator recommendation visible as secondary provenance rather than overwriting it

#### Scenario: Adapter and tracking label remain visible
- **WHEN** an Estimated task offers launch controls
- **THEN** the control SHALL show the Worker Adapter identity separately from the tracking label or usage-authority mode
