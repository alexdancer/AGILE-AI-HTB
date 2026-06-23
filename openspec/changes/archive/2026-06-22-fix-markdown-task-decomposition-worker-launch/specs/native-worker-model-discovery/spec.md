## MODIFIED Requirements

### Requirement: Worker model recommendation constraints
The system SHALL recommend Worker execution models only from models discovered for a verified Worker Harness unless the User manually overrides with an explicit compatible model. When the control-plane estimator recommends a model that is not present in the discovered inventory, the system SHALL select a discovered model by task estimate, complexity, and model-name suitability rather than by raw discovery order.

#### Scenario: Estimate with discovered worker models
- **WHEN** the control-plane model estimates a task and a verified Worker Harness has discovered models
- **THEN** the recommendation uses a model from that Worker Harness's discovered model set
- **AND** the recommendation records metadata explaining whether the estimator model was matched directly or constrained to a discovered substitute

#### Scenario: No discovered worker models
- **WHEN** no Worker Harness model inventory is available
- **THEN** the system may estimate task size but does not mark the task launch-ready with a static or assumed Worker model

#### Scenario: Simple task avoids heavyweight first discovered model
- **WHEN** a simple or small estimated task is constrained to an OpenCode inventory where `opencode/big-pickle` appears before lightweight models
- **THEN** the selected Worker model is a discovered lightweight model when one is available
- **AND** the selected Worker model is not chosen solely because it appears first in the discovered inventory

#### Scenario: Large task may use heavyweight model
- **WHEN** a large or high-complexity estimated task is constrained to a discovered inventory that includes heavyweight models
- **THEN** the system may select a heavyweight discovered model when the estimate and complexity justify it
- **AND** the constraint metadata records the original estimator recommendation, available models, selected model, and reason
