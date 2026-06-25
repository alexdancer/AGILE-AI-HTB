## MODIFIED Requirements

### Requirement: Discovered model inventory
The system SHALL persist discovered Worker Harness models with their adapter id, provider/model identifier, discovery timestamp, and availability status. The system SHALL preserve the discovered inventory separately from the operator-approved Worker model allow-list used for governed recommendation and launch.

#### Scenario: Model inventory displayed
- **WHEN** the User views Worker Harness settings
- **THEN** the system shows discovered models for each adapter and indicates when discovery last succeeded or failed
- **AND** the system indicates which discovered models are currently allowed for governed AGILE use

#### Scenario: Discovery preserves curated allow-list
- **WHEN** an adapter already has an operator-approved allowed model subset
- **AND** model discovery runs again and returns additional models
- **THEN** the discovered inventory is updated
- **AND** the allowed subset is not silently expanded to include newly discovered models

### Requirement: Worker model recommendation constraints
The system SHALL recommend Worker execution models only from the selected adapter's operator-approved allowed Worker model subset. When the control-plane estimator recommends a model that is not allowed for the selected adapter, the system SHALL select an allowed model by task estimate, complexity, and model-name suitability rather than by raw discovery order.

#### Scenario: Estimate with allowed worker models
- **WHEN** the control-plane model estimates a task and a verified Worker Harness has allowed models
- **THEN** the recommendation uses a model from that Worker Harness's allowed model set
- **AND** the recommendation records metadata explaining whether the estimator model was matched directly or constrained to an allowed substitute

#### Scenario: No allowed worker models
- **WHEN** no allowed Worker Harness model inventory is available
- **THEN** the system may estimate task size but does not mark the task launch-ready with a static or assumed Worker model

#### Scenario: Simple task avoids heavyweight first discovered model
- **WHEN** a simple or small estimated task is constrained to an OpenCode allow-list where `opencode/big-pickle` appears before lightweight models
- **THEN** the selected Worker model is an allowed lightweight model when one is available
- **AND** the selected Worker model is not chosen solely because it appears first in the discovered inventory

#### Scenario: Large task may use heavyweight model
- **WHEN** a large or high-complexity estimated task is constrained to an allowed model set that includes heavyweight models
- **THEN** the system may select a heavyweight allowed model when the estimate and complexity justify it
- **AND** the constraint metadata records the original estimator recommendation, available allowed models, selected model, and reason
