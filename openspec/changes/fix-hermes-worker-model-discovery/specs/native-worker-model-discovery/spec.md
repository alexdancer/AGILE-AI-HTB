## ADDED Requirements

### Requirement: Hermes model inventory is curated
The system SHALL use a curated Hermes Worker model inventory instead of invoking a native Hermes model-discovery command when discovering models for the Hermes Worker Adapter.

#### Scenario: Hermes discovery uses curated inventory
- **WHEN** an operator runs model discovery for the Hermes Worker Adapter
- **THEN** the system SHALL NOT execute `hermes models`
- **AND** the discovered or selectable Hermes Worker model inventory SHALL contain the configured curated Hermes Worker model IDs
- **AND** the discovery evidence SHALL identify the inventory as curated rather than native CLI output

#### Scenario: Hermes curated discovery preserves allowed subset
- **WHEN** Hermes already has an operator-approved allowed model subset
- **AND** curated discovery runs again
- **THEN** the curated inventory is refreshed
- **AND** the allowed subset is not silently expanded beyond the operator-approved models

#### Scenario: Hermes discovery remains separate from launch verification
- **WHEN** Hermes curated model discovery succeeds
- **THEN** the system SHALL treat discovery as model inventory only
- **AND** the system SHALL still require the selected Hermes Worker model and tracking mode to pass the normal launch guardrails before governed AGILE Board launch
