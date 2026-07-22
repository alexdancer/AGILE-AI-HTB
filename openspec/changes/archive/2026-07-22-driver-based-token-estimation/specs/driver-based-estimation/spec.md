## ADDED Requirements

### Requirement: Estimator emits Estimation Drivers instead of owning the token magnitude
The Estimator LLM SHALL emit structural Estimation Drivers — `files_to_read`, `files_to_modify`, `expected_turns`, `needs_test_run` — alongside the existing `complexity` and `confidence`, and SHALL NOT own the final token magnitude. Estimation validation SHALL require the driver fields and SHALL reject a response that supplies a top-level authoritative final token estimate as the answer.

#### Scenario: Valid drivers accepted
- **WHEN** the estimator LLM returns valid structured JSON with `files_to_read`, `files_to_modify`, `expected_turns`, `needs_test_run`, `complexity`, and `confidence`
- **THEN** estimation validation SHALL succeed
- **AND** the drivers SHALL be persisted with the resulting task

#### Scenario: Missing driver fields rejected
- **WHEN** the estimator LLM response omits any required driver field
- **THEN** estimation validation SHALL fail with a validation error
- **AND** no automatic token estimate SHALL be produced

### Requirement: Token estimate is computed arithmetically from per-adapter coefficients
The harness SHALL compute the stored `token_estimate` from the Estimation Drivers and per-Worker-Adapter, per-model coefficients using `Ê = T·(a·r + b·m) + (g/2)·T(T−1) + p·T + k·τ`, where `r`/`m`/`T`/`τ` are the drivers and `a`/`b`/`g`/`p`/`k` are the coefficients. The computed value SHALL retain the name `token_estimate` so downstream model routing, stored `estimate_tokens`, and board rendering are unchanged.

#### Scenario: Estimate computed from drivers and coefficients
- **WHEN** valid drivers are produced for a task under a selected Worker Adapter and model
- **THEN** the harness SHALL resolve the adapter/model coefficients and compute `token_estimate` via the equation
- **AND** deterministic adapter-aware routing SHALL receive that computed `token_estimate`

#### Scenario: Estimate is quadratic in expected turns
- **WHEN** two otherwise identical driver sets differ only in `expected_turns`
- **THEN** the computed `token_estimate` SHALL grow faster than linearly in `expected_turns` because of the `(g/2)·T(T−1)` term

### Requirement: Coefficients ship as a checked-in provenance-tagged set with a default fallback
The system SHALL ship estimation coefficients as a checked-in file in which each factor is tagged `seed` or `fitted(n)`. The context-growth factor `g` SHALL ship as an honest `seed` (it cannot be fitted while the recorded demo pins cache counters to zero) and the harness SHALL NOT fabricate cache-bearing demo evidence to present `g` as fitted. A `default` coefficient block SHALL resolve any adapter/model with no specific entry; using the default SHALL NOT be treated as an estimator failure.

#### Scenario: Unknown adapter resolves to default coefficients
- **WHEN** a task is estimated under an adapter/model with no specific coefficient block
- **THEN** the harness SHALL resolve the `default` block and compute a normal estimate
- **AND** the estimate SHALL NOT be downgraded to a manual-required state solely for using defaults

#### Scenario: Factor provenance is available on the estimate
- **WHEN** a `token_estimate` is computed
- **THEN** the per-factor provenance (`seed` or `fitted(n)`) used SHALL be available for display and audit

### Requirement: LLM guess is retained as a shadow with a disagreement signal
The system SHALL persist the LLM's own token guess as a shadow (`shadow_token_estimate`) and SHALL record `estimate_disagreement = |computed − shadow| / computed` as a quality signal in task metadata. The shadow SHALL NOT be authoritative and SHALL NOT feed model routing or budget accounting.

#### Scenario: Shadow and disagreement persisted
- **WHEN** a `token_estimate` is computed and the estimator also returned a `shadow_token_estimate`
- **THEN** task metadata SHALL include the shadow value and the computed disagreement ratio
- **AND** model routing and budget accounting SHALL use only the computed `token_estimate`

### Requirement: Driver arithmetic is the primary path with manual-estimate-only fallback
Driver arithmetic SHALL be the primary estimation path, not a fallback layered under a heuristic. An Estimator LLM failure, or invalid or missing drivers, SHALL yield no automatic estimate — the task SHALL require a manual estimate — and the harness SHALL NOT silently substitute a heuristic token number.

#### Scenario: Estimator failure requires manual estimate
- **WHEN** the estimator LLM call fails or returns a response without valid drivers
- **THEN** the task SHALL be created in an `Estimated` state flagged as requiring a manual estimate
- **AND** no automatic or heuristic `token_estimate` SHALL be stored
