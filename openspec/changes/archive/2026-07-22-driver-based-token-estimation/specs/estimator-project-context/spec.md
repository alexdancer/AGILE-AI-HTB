## MODIFIED Requirements

### Requirement: Estimator output excludes Worker model choice
The estimator SHALL produce Estimation Drivers and confidence evidence without owning Worker model selection or the final token magnitude. `estimate_task()` SHALL NOT require the estimator LLM response to include a Worker `recommended_model`; deterministic adapter-aware routing SHALL choose the Worker recommendation after estimator validation succeeds. The estimator response SHALL supply the Estimation Drivers (`files_to_read`, `files_to_modify`, `expected_turns`, `needs_test_run`) plus `complexity`, `confidence`, and a non-authoritative `shadow_token_estimate`; the harness SHALL compute the stored `token_estimate` arithmetically from those drivers.

#### Scenario: Estimator returns drivers and shadow only
- **WHEN** the estimator LLM returns valid structured JSON with the Estimation Drivers, complexity, confidence, rationale, assumptions, risk flags, budget note, source, and a `shadow_token_estimate`
- **THEN** estimation validation SHALL succeed without a `recommended_model` field
- **AND** the harness SHALL compute the stored `token_estimate` from the drivers rather than accepting an LLM-owned final estimate
- **AND** model routing SHALL run after validation to select or omit the task Worker recommendation

#### Scenario: Estimator includes obsolete model field
- **WHEN** the estimator LLM returns an extra `recommended_model` field under the new contract
- **THEN** validation SHALL reject the extra field or ignore it according to the implementation's strict-output policy
- **AND** the LLM-provided model SHALL NOT become the stored task recommendation

#### Scenario: Existing project context remains estimator input
- **WHEN** a project-board task is estimated
- **THEN** the estimator still receives the bounded Repo Context Brief and calibration summary when available
- **AND** the estimator does not receive Worker Adapter credentials or native Worker auth state
