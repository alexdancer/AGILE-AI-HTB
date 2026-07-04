## MODIFIED Requirements

### Requirement: Worker model routing constraints
The system SHALL route Worker execution models only from the selected or default adapter's operator-approved allowed Worker model subset. Task Estimation SHALL provide token estimate and complexity evidence, and deterministic routing SHALL use that evidence with guardrail model-routing policy, budget clamp, and adapter allowed models to select the stored routed task model. When no approved allowed Worker model subset is available, the system MAY estimate task size but SHALL NOT store a static or assumed Worker model.

#### Scenario: Estimate with allowed worker models
- **WHEN** the control-plane model estimates a task and a verified Worker Harness has allowed models
- **THEN** deterministic routing uses a model from that Worker Harness's allowed model set
- **AND** routing metadata explains whether the guardrail policy candidate was matched directly or constrained to an allowed substitute

#### Scenario: No allowed worker models
- **WHEN** no allowed Worker Harness model inventory is available
- **THEN** the system may estimate task size but does not mark the task launch-ready with a static or assumed Worker model
- **AND** the task metadata records that Worker model setup is incomplete

#### Scenario: Simple task avoids heavyweight first discovered model
- **WHEN** a simple or small estimated task is constrained to an OpenCode allow-list where `opencode/big-pickle` appears before lightweight models
- **THEN** the selected Worker model is an allowed lightweight model when one is available
- **AND** the selected Worker model is not chosen solely because it appears first in the discovered inventory

#### Scenario: Large task may use heavyweight model
- **WHEN** a large or high-complexity estimated task is constrained to an allowed model set that includes heavyweight models
- **THEN** the system may select a heavyweight allowed model when the estimate and complexity justify it
- **AND** the constraint metadata records the guardrail policy candidate, available allowed models, selected model, and reason

#### Scenario: Estimator cannot authorize an unavailable model
- **WHEN** the estimator's complexity evidence would map to a guardrail model that is not allowed by the selected Worker Adapter
- **THEN** the stored routed task model SHALL be an allowed substitute or absent
- **AND** the system SHALL NOT persist the unavailable guardrail model as the primary `recommended_model`
