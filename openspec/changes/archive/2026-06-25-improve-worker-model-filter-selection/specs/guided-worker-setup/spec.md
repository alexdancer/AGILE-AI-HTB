## MODIFIED Requirements

### Requirement: Worker Setup presents one active adapter workflow
The Worker Setup page SHALL present a guided setup workflow for one active Worker Adapter at a time while still exposing all supported adapter presets as selectable options. The workflow SHALL let the operator choose which discovered Worker models are allowed for governed AGILE recommendations and board launches, and SHALL provide filtering and visible bulk selection controls when the discovered model list is shown.

#### Scenario: Default adapter exists
- **WHEN** an operator opens `/settings/workers`
- **AND** one adapter has `is_default` set
- **THEN** the guided setup workflow is populated with that adapter
- **AND** the adapter chooser shows that adapter as the active/default selection

#### Scenario: No default adapter exists
- **WHEN** an operator opens `/settings/workers`
- **AND** no adapter has `is_default` set
- **THEN** the guided setup workflow is populated with the first available seeded adapter
- **AND** the page indicates that no default adapter has been saved yet

#### Scenario: Operator selects another adapter
- **WHEN** an operator chooses a different adapter from the Worker Adapter selector
- **THEN** the setup workflow displays that adapter's workdir, discovered models, verification status, and readiness state
- **AND** saving the setup can designate that adapter as the default Worker Adapter

#### Scenario: Operator selects allowed models
- **WHEN** model discovery has returned models for the active Worker Adapter
- **THEN** the setup workflow shows the discovered models as selectable allowed-model options
- **AND** saving the selection persists the subset used by estimates, board dropdowns, and launch guardrails

#### Scenario: Operator filters discovered model options
- **WHEN** model discovery has returned a long model list for the active Worker Adapter
- **AND** the operator enters a filter term in the discovered model selector
- **THEN** the setup workflow shows only discovered model options whose model id matches the filter term
- **AND** already-selected hidden options remain selected unless the operator changes them

#### Scenario: Operator checks visible discovered models
- **WHEN** the operator has filtered the discovered model selector
- **AND** clicks `Check visible`
- **THEN** every currently visible discovered model option is selected
- **AND** non-visible discovered model options are not changed

#### Scenario: Operator unchecks visible discovered models
- **WHEN** the operator has filtered the discovered model selector
- **AND** clicks `Uncheck visible`
- **THEN** every currently visible discovered model option is deselected
- **AND** non-visible discovered model options are not changed
