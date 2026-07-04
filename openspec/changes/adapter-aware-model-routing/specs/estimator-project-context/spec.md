## ADDED Requirements

### Requirement: Estimator output excludes Worker model choice
The estimator SHALL produce task sizing and confidence evidence without owning Worker model selection. `estimate_task()` SHALL NOT require the estimator LLM response to include a Worker `recommended_model`; deterministic adapter-aware routing SHALL choose the Worker recommendation after estimator validation succeeds.

#### Scenario: Estimator returns sizing fields only
- **WHEN** the estimator LLM returns valid structured JSON with token estimate, complexity, confidence, rationale, assumptions, risk flags, budget note, and source
- **THEN** estimation validation SHALL succeed without a `recommended_model` field
- **AND** model routing SHALL run after validation to select or omit the task Worker recommendation

#### Scenario: Estimator includes obsolete model field
- **WHEN** the estimator LLM returns an extra `recommended_model` field under the new contract
- **THEN** validation SHALL reject the extra field or ignore it according to the implementation's strict-output policy
- **AND** the LLM-provided model SHALL NOT become the stored task recommendation

#### Scenario: Existing project context remains estimator input
- **WHEN** a project-board task is estimated
- **THEN** the estimator still receives the bounded Repo Context Brief and calibration summary when available
- **AND** the estimator does not receive Worker Adapter credentials or native Worker auth state

### Requirement: Estimation response includes routed model provenance
The `/estimate` response SHALL include the deterministic routing result alongside estimator sizing fields so API callers and board rendering can distinguish estimator evidence from Worker model routing evidence.

#### Scenario: Routed model selected
- **WHEN** estimation succeeds and adapter-aware routing selects an allowed Worker model
- **THEN** the response SHALL include `recommended_model` equal to the selected allowed Worker model
- **AND** task metadata SHALL include routing provenance

#### Scenario: Routed model unavailable
- **WHEN** estimation succeeds but no allowed Worker model can be selected
- **THEN** the response SHALL include no static Worker model or SHALL include `recommended_model=null`
- **AND** task metadata SHALL identify the missing adapter/allowed-model setup state
