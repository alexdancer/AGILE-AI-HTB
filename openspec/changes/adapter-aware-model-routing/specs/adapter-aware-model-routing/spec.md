## ADDED Requirements

### Requirement: Deterministic adapter-aware Worker model routing
The system SHALL select the stored routed Worker model deterministically from the selected or default Worker Adapter's operator-approved allowed Worker model subset after Task Estimation produces token estimate and complexity evidence.

#### Scenario: Recommended model is allowed by selected adapter
- **WHEN** an operator estimates a task with selected adapter `opencode`
- **AND** `opencode` has allowed Worker models `["opencode/gpt-5.1", "opencode/gpt-5.4-mini"]`
- **THEN** the persisted task `recommended_model` SHALL be one of those allowed Worker model IDs
- **AND** the task metadata SHALL record the selected adapter id and routing reason

#### Scenario: Default adapter is used when no adapter is selected
- **WHEN** an operator estimates a task without providing an adapter id
- **AND** a default Worker Adapter exists with allowed Worker models
- **THEN** the model router SHALL use the default adapter's allowed Worker model subset for routing

#### Scenario: No adapter has allowed models
- **WHEN** an operator estimates a task and no selected or default Worker Adapter has operator-approved allowed models
- **THEN** the system MAY persist token estimate and complexity evidence
- **AND** the system SHALL NOT persist a static assumed Worker model
- **AND** the task metadata SHALL explain that Worker model setup is incomplete

### Requirement: Guardrail routing policy feeds deterministic routing
The system SHALL use `guardrails.yaml` model-routing policy as deterministic routing input rather than as the estimator LLM's source of authority for Worker model choice.

#### Scenario: Guardrail policy candidate maps directly to allowed model
- **WHEN** the estimator classifies a task as `modest`
- **AND** guardrails map `modest` to `claude-sonnet-4-6`
- **AND** the selected adapter allows `claude-sonnet-4-6`
- **THEN** the router SHALL select `claude-sonnet-4-6`
- **AND** metadata SHALL record a direct guardrail-policy match

#### Scenario: Guardrail policy candidate is unavailable for adapter
- **WHEN** the estimator classifies a task as `modest`
- **AND** guardrails map `modest` to a model that the selected adapter does not allow
- **AND** the selected adapter has other allowed Worker models
- **THEN** the router SHALL select an allowed Worker model substitute
- **AND** metadata SHALL record the original guardrail policy candidate, selected substitute, allowed model list, and substitution reason

### Requirement: Budget-aware clamp is enforced before final routing
The system SHALL enforce guardrails `budget_aware_clamp` in deterministic routing before storing the routed task model. When remaining daily budget is below the configured threshold, the router SHALL downgrade the routing tier by one step when a lower tier exists, then choose an allowed Worker model for that downgraded tier.

#### Scenario: Budget clamp downgrades complex task
- **WHEN** a task is classified as `complex`
- **AND** remaining daily budget divided by daily cap is below `budget_aware_clamp.remaining_daily_threshold`
- **THEN** the router SHALL use the next lower routing tier before choosing the final allowed Worker model
- **AND** metadata SHALL record `budget_clamped=true`, original tier, clamped tier, and note text

#### Scenario: Budget clamp does not bypass adapter allowed models
- **WHEN** budget clamp selects a lower-tier guardrail policy candidate
- **AND** that candidate is not in the selected adapter's allowed Worker model subset
- **THEN** the final task recommendation SHALL still be chosen only from the selected adapter's allowed Worker models

### Requirement: Routing provenance is preserved
The system SHALL preserve bounded routing provenance in task metadata so operators and tests can see why a model was or was not recommended.

#### Scenario: Successful routing metadata
- **WHEN** the router selects a Worker model
- **THEN** task metadata SHALL include selected adapter id, selected model, original complexity, final routing tier, guardrail policy candidate, allowed-model constraint state, and reason

#### Scenario: No routed model metadata
- **WHEN** the router cannot select a Worker model because no approved allowed model subset exists
- **THEN** task metadata SHALL include a no-recommendation state and setup guidance without inventing a model id
