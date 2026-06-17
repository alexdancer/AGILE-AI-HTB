## MODIFIED Requirements

### Requirement: Operator can set adapter working directory

The Workers settings page SHALL provide a guided Worker Setup form for the active adapter allowing the operator to set or change the working directory. The form SHALL POST to `/settings/workers/{adapter_id}/configure` which updates the adapter record and redirects back to the Workers page.

#### Scenario: Setting workdir for an unconfigured adapter

- **WHEN** operator enters a valid filesystem path in the active adapter workdir form and submits
- **THEN** the adapter's workdir is updated in the database
- **AND** the Workers page shows the new workdir value in the guided setup workflow
- **AND** the adapter's readiness summary no longer reports the project folder as missing

#### Scenario: Setting workdir to a non-existent path

- **WHEN** operator enters a path that does not exist on the filesystem
- **THEN** the workdir is still accepted
- **AND** subsequent verification will fail with "Worker adapter workdir does not exist"
- **AND** the readiness summary shows the adapter as not launch-ready

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
