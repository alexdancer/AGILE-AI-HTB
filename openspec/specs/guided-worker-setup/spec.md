# guided-worker-setup

## Purpose

Define the simplified Worker Setup experience that guides operators through configuring one active Worker Adapter, verifying token tracking, and understanding launch readiness without exposing raw debug data as primary UI.

## Requirements

### Requirement: Worker Setup presents one active adapter workflow
The Worker Setup page SHALL present a guided setup workflow for one active Worker Adapter at a time while still exposing all supported adapter presets as selectable options. The workflow SHALL let the operator choose which discovered Worker models are allowed for governed AGILE recommendations and board launches.

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

### Requirement: Worker Setup shows launch readiness and next action
The Worker Setup page SHALL show a single user-facing readiness summary for the active adapter that explains whether it is launch-ready and what action is required next.

#### Scenario: Adapter is launch-ready
- **WHEN** the active adapter is configured, has at least one allowed compatible model, and has passed token-tracking verification
- **THEN** the page shows the adapter as launch-ready
- **AND** the summary indicates the AGILE Board can launch governed work with this adapter

#### Scenario: Connected project is not configured
- **WHEN** no connected project exists
- **THEN** the project setup page directs the operator to connect a project folder

#### Scenario: Adapter verification is missing
- **WHEN** the active adapter is configured but has not passed token-tracking verification
- **THEN** the page shows the adapter as not launch-ready
- **AND** the next action tells the operator to run governed launch verification

#### Scenario: Adapter verification failed
- **WHEN** the active adapter's last verification failed
- **THEN** the page shows the adapter as not launch-ready
- **AND** the summary includes the failure reason without requiring the operator to inspect raw evidence JSON

#### Scenario: No allowed models selected
- **WHEN** the active adapter has discovered models but no models are allowed
- **THEN** the page shows the adapter as not launch-ready
- **AND** the next action tells the operator to allow at least one discovered Worker model

### Requirement: Worker Setup hides debug details by default
The Worker Setup page SHALL keep low-level diagnostics and evidence available under an Advanced details section instead of showing them in the primary setup workflow.

#### Scenario: Advanced details collapsed
- **WHEN** an operator opens `/settings/workers`
- **THEN** raw verification evidence, executable path, command path, proxy URL, tracking mode labels, and model discovery JSON are not shown as primary setup fields
- **AND** the page provides an Advanced details disclosure for troubleshooting

#### Scenario: Advanced details expanded
- **WHEN** an operator opens or expands Advanced details for the active adapter
- **THEN** the page shows cached diagnostics, command/executable details, tracking mode details, model discovery evidence, and verification evidence when available

### Requirement: Worker Setup preserves model layer separation
The Worker Setup page SHALL configure Worker/coding harness adapters and SHALL NOT present generic provider API key setup as part of the Worker Adapter workflow.

#### Scenario: Operator configures OpenCode worker adapter
- **WHEN** an operator selects OpenCode on the Worker Setup page
- **THEN** the page asks for Worker Adapter setup inputs such as project folder, model discovery/selection, and token-tracking verification
- **AND** the page does not ask for a generic `PROVIDER_API_KEY` as if it were required for native Worker setup
