## ADDED Requirements

### Requirement: Operator can set adapter working directory
The Workers settings page SHALL provide a form per adapter card allowing the operator to set or change the working directory. The form SHALL POST to `/settings/workers/{adapter_id}/configure` which updates the adapter record and redirects back to the Workers page.

#### Scenario: Setting workdir for an unconfigured adapter
- **WHEN** operator enters a valid filesystem path in the workdir form and submits
- **THEN** the adapter's workdir is updated in the database
- **AND** the Workers page shows the new workdir value
- **AND** the adapter's configured status pill updates to "configured"

#### Scenario: Setting workdir to a non-existent path
- **WHEN** operator enters a path that does not exist on the filesystem
- **THEN** the workdir is still accepted (validation happens at verification time)
- **AND** subsequent verification will fail with "Worker adapter workdir does not exist"

### Requirement: Operator can set default adapter
The Workers settings page SHALL provide a control to designate one adapter as the default. Setting an adapter as default SHALL clear the default flag from all other adapters.

#### Scenario: Setting first default adapter
- **WHEN** operator clicks "Set as default" on an unconfigured adapter
- **THEN** that adapter's `is_default` flag is set to true
- **AND** no other adapter has `is_default` set

#### Scenario: Changing default adapter
- **WHEN** adapter A is default and operator sets adapter B as default
- **THEN** adapter A's `is_default` becomes false
- **AND** adapter B's `is_default` becomes true

### Requirement: Diagnostics shown for all adapter kinds
The Workers settings page SHALL show installation diagnostics (installed, callable, command, executable, version, failure reason) for every seeded adapter kind, not only OpenCode. Diagnostics SHALL be cached in the adapter config to avoid subprocess calls on every page render.

#### Scenario: Diagnostics for installed adapter
- **WHEN** an adapter's CLI binary is on PATH and responds to `--version`
- **THEN** the adapter card shows `installed: yes`, `callable: yes`, and the version string

#### Scenario: Diagnostics for missing adapter
- **WHEN** an adapter's CLI binary is not found on PATH
- **THEN** the adapter card shows `installed: no`, `callable: no`, and the failure reason

#### Scenario: Cached diagnostics survive page reload
- **WHEN** diagnostics have been run within the last 5 minutes
- **THEN** loading the Workers page SHALL display cached results without running subprocesses

### Requirement: Operator can refresh diagnostics
Each adapter card SHALL include a "Refresh diagnostics" control that re-runs `detect_worker_adapter()` immediately and updates the cache.

#### Scenario: Manual refresh after installing a CLI
- **WHEN** operator installs a previously-missing adapter CLI
- **AND** clicks "Refresh diagnostics"
- **THEN** diagnostics re-run and show `installed: yes`
