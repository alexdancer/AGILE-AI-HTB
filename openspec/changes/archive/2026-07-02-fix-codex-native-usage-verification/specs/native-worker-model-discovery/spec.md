## ADDED Requirements

### Requirement: Codex model inventory is curated
The system SHALL use a curated Codex Worker model inventory instead of invoking a native Codex model-discovery command.

#### Scenario: Codex discovery uses curated inventory
- **WHEN** an operator runs model discovery for the Codex Worker Adapter
- **THEN** the system SHALL NOT execute an unsupported or interactive Codex model-listing command
- **AND** the discovered or selectable Codex Worker model inventory SHALL contain exactly `gpt-5.4` and `gpt-5.4-mini`
- **AND** the discovery evidence SHALL identify the inventory as curated rather than native CLI output

#### Scenario: Stale Codex seeded defaults are not allowed models
- **WHEN** a Codex adapter row contains only stale seeded defaults such as `5.3-codex-spark`, `5.4`, `5.4-mini`, `5.5`, `gpt-5.1-codex`, or `openai/gpt-4.1-mini`
- **THEN** the system SHALL treat that row as having no operator-approved allowed Codex model subset
- **AND** normal governed launch SHALL remain unavailable until the operator approves current Codex model IDs

#### Scenario: Codex curated discovery preserves allowed subset
- **WHEN** Codex already has an operator-approved allowed model subset
- **AND** curated discovery runs again
- **THEN** the curated inventory is refreshed
- **AND** the allowed subset is not silently expanded beyond the operator-approved models
