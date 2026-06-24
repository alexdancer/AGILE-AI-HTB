# adapter-configuration-ui

## Purpose

Enable operators to configure Worker Adapter presets through the portal UI — designating default adapters, viewing installation diagnostics for all adapter kinds, refreshing diagnostics on demand, and keeping project root selection in the connected project workspace.

## Requirements

### Requirement: Worker Setup does not own project workdir
The Workers settings page SHALL NOT present adapter workdir as the normal project root selection mechanism. Project root selection SHALL come from connected project workspace state, while Worker Adapter setup SHALL remain focused on CLI/tracking readiness and default adapter selection.

#### Scenario: Saving adapter settings ignores legacy workdir input
- **WHEN** operator submits `/settings/workers/{adapter_id}/configure` with a legacy `workdir` form field
- **THEN** the adapter's workdir is not changed
- **AND** the adapter default selection is still applied when requested
- **AND** the Workers page explains that project root is managed by the connected project workspace

#### Scenario: Connected project supplies launch root
- **WHEN** operator connects a project through the project workspace flow
- **THEN** the connected project root is persisted as project workspace state
- **AND** Worker Adapter settings do not duplicate that root into adapter configuration

### Requirement: Operator can set default adapter
The Workers settings page SHALL provide a control in the guided setup workflow to designate the active adapter as the default. Setting an adapter as default SHALL clear the default flag from all other adapters.

#### Scenario: Setting first default adapter
- **WHEN** operator saves the active adapter as default
- **THEN** that adapter's `is_default` flag is set to true
- **AND** no other adapter has `is_default` set
- **AND** the Workers page opens with that adapter active on the next load

#### Scenario: Changing default adapter
- **WHEN** adapter A is default and operator sets adapter B as default
- **THEN** adapter A's `is_default` becomes false
- **AND** adapter B's `is_default` becomes true
- **AND** the guided setup workflow shows adapter B as the default adapter

### Requirement: Diagnostics shown for all adapter kinds
The Workers settings page SHALL expose installation diagnostics for every seeded adapter kind, but low-level diagnostics (installed, callable, command, executable, version, failure reason) SHALL be grouped under Advanced details rather than shown as primary setup content. Diagnostics SHALL be cached in the adapter config to avoid subprocess calls on every page render.

#### Scenario: Diagnostics for installed adapter
- **WHEN** an adapter's CLI binary is on PATH and responds to `--version`
- **THEN** the adapter chooser or readiness area can indicate that the adapter is detected
- **AND** Advanced details shows `installed: yes`, `callable: yes`, and the version string

#### Scenario: Diagnostics for missing adapter
- **WHEN** an adapter's CLI binary is not found on PATH
- **THEN** the adapter chooser or readiness area can indicate that the adapter is not detected
- **AND** Advanced details shows `installed: no`, `callable: no`, and the failure reason

#### Scenario: Cached diagnostics survive page reload
- **WHEN** diagnostics have been run within the last 5 minutes
- **THEN** loading the Workers page SHALL display cached results without running subprocesses

### Requirement: Operator can refresh diagnostics
The guided Worker Setup page SHALL include a "Refresh diagnostics" control for the active adapter that re-runs `detect_worker_adapter()` immediately and updates the cache.

#### Scenario: Manual refresh after installing a CLI
- **WHEN** operator installs a previously-missing adapter CLI
- **AND** selects that adapter in Worker Setup
- **AND** clicks "Refresh diagnostics"
- **THEN** diagnostics re-run and the readiness/advanced details reflect the updated detection result

### Requirement: Worker Setup labels tracking mode strength
The Workers settings page SHALL display canonical tracking labels and separate launch readiness from runtime request guardrail availability and accounting authority.

#### Scenario: Proxy-governed adapter label
- **WHEN** Worker Setup renders an adapter verified with `proxy_governed` tracking mode
- **THEN** it shows `Tracking: Governed via Harness Proxy`
- **AND** it shows `Runtime request guardrails: Available`
- **AND** it shows `Accounting: Budget-authoritative during run`

#### Scenario: Native usage adapter label
- **WHEN** Worker Setup renders an adapter verified with `native_usage` tracking mode
- **THEN** it shows `Tracking: Tracked via Native Usage`
- **AND** it shows `Runtime request guardrails: Not available`
- **AND** it shows `Accounting: Budget-authoritative after run`

#### Scenario: Observed-only adapter label
- **WHEN** Worker Setup renders an adapter verified with `observed_only` tracking mode
- **THEN** it shows `Tracking: Observed Only`
- **AND** it shows `Runtime request guardrails: Not available`
- **AND** it shows `Accounting: Not budget-authoritative`
- **AND** it does not mark the adapter launchable for governed board tasks
