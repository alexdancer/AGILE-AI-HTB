## MODIFIED Requirements

### Requirement: Launch controls preserve model-layer clarity
Board launch controls SHALL keep Worker Adapter selection, Worker model selection, and estimator/routing provenance visually distinct. The stored task recommendation SHALL represent the deterministic adapter-aware Worker model routing result when available, while metadata SHALL preserve estimator complexity evidence and any guardrail policy candidate that was substituted. Launch-time operator overrides remain visible as selected/launched Worker model evidence.

#### Scenario: Recommendation is adapter-compatible before launch
- **WHEN** an Estimated task offers launch controls
- **AND** the task has a `recommended_model`
- **THEN** the recommendation SHALL be compatible with the task's selected/default Worker Adapter allowed model subset at estimation time
- **AND** the control SHALL still show the Worker Adapter identity separately from the tracking label or usage-authority mode

#### Scenario: Launch model differs from routed recommendation
- **WHEN** a task has a recommended model and a different selected or launched Worker model
- **THEN** the board SHALL display the selected/launched Worker model as the primary run model
- **AND** it SHALL keep the routed recommendation and estimator sizing evidence visible as secondary provenance rather than overwriting them

#### Scenario: No routed recommendation exists
- **WHEN** an Estimated task has token estimate evidence but no routed Worker model because no allowed model subset exists
- **THEN** the board SHALL avoid displaying a fake default model
- **AND** launch controls SHALL direct the operator to Worker Setup or allowed-model configuration before launch can proceed

#### Scenario: Adapter and tracking label remain visible
- **WHEN** an Estimated task offers launch controls
- **THEN** the control SHALL show the Worker Adapter identity separately from the tracking label or usage-authority mode
