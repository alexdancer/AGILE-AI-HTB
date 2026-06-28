# guided-worker-setup

## Purpose

Define the simplified Worker Setup experience that guides operators through configuring one active Worker Adapter, verifying token tracking, and understanding launch readiness without exposing raw debug data as primary UI.

## Requirements

### Requirement: Worker Adapter public setup matrix
The public onboarding documentation SHALL provide a Worker Adapter setup matrix for first-class adapter families.

#### Scenario: Operator reads Worker Adapter matrix
- **WHEN** an operator reads public Worker setup guidance
- **THEN** the matrix SHALL cover OpenCode, Claude Code, Codex, and Hermes
- **AND** each row SHALL separate adapter identity, Worker CLI auth source, available tracking modes, launchable evidence, and common failure modes

#### Scenario: Matrix distinguishes tracking modes
- **WHEN** the matrix describes `proxy_governed`, `native_usage`, or `observed_only`
- **THEN** it SHALL state whether runtime request guardrails are available and whether accounting is budget-authoritative
- **AND** it SHALL state that `observed_only` is diagnostic-only and not launchable from the normal AGILE Board

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
The Worker Setup page and public setup guidance SHALL configure Worker/coding harness adapters and SHALL NOT present the control-plane API key or any generic provider API key as native Worker Adapter authentication.

#### Scenario: Operator configures OpenCode worker adapter
- **WHEN** an operator selects OpenCode on the Worker Setup page
- **THEN** the page asks for Worker Adapter setup inputs such as project folder, model discovery/selection, and token-tracking verification
- **AND** the page does not ask for a generic `PROVIDER_API_KEY` as if it were required for native Worker setup

#### Scenario: Operator already configured control-plane key
- **WHEN** an operator has pasted a control-plane API key through `/settings/control-plane`
- **THEN** Worker setup guidance SHALL still state that native OpenCode, Claude Code, Codex, Hermes, or other Worker CLIs may require their own installed CLI auth/config
- **AND** it SHALL NOT imply that the control-plane API key automatically configures those Worker CLIs

### Requirement: Setup pages show the next missing setup action
Setup and Worker Adapter pages SHALL identify the next missing action needed to make the Portal launch-ready.

#### Scenario: Worker setup highlights next missing action
- **WHEN** an authenticated operator opens Worker Adapter setup and the active adapter is not launchable
- **THEN** the page SHALL show the next missing setup action such as select default adapter, discover models, allow models, verify tracking, or connect/open a project when that context is missing
- **AND** the page SHALL link or focus the existing control that completes that action

#### Scenario: Launch-ready setup shows board action
- **WHEN** required setup is complete for launching governed tasks
- **THEN** the setup surface SHALL show a launch-ready state and link to the appropriate project board or project selection surface

### Requirement: Advanced diagnostics are secondary
Worker/setup diagnostics SHALL remain available without overwhelming the first setup path.

#### Scenario: Diagnostic detail remains available
- **WHEN** adapter diagnostics, verification evidence, tracking details, or model discovery evidence exist
- **THEN** the page SHALL keep that evidence available behind native disclosure or an advanced details section

#### Scenario: Primary setup path is readable
- **WHEN** an operator is completing setup for the first time
- **THEN** advanced diagnostics SHALL NOT be required reading before the next missing action is visible
