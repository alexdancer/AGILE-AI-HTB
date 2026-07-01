## ADDED Requirements

### Requirement: Claude Code model inventory is curated
The system SHALL use a curated Claude Code Worker model inventory instead of invoking a native Claude Code model-discovery command.

#### Scenario: Claude Code discovery uses curated inventory
- **WHEN** an operator runs model discovery for the Claude Code Worker Adapter
- **THEN** the system SHALL NOT execute `claude models`
- **AND** the discovered or selectable Claude Code Worker model inventory SHALL contain exactly `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, and `claude-haiku-4-5`
- **AND** the discovery evidence SHALL identify the inventory as curated rather than native CLI output

#### Scenario: Claude Code curated discovery preserves allowed subset
- **WHEN** Claude Code already has an operator-approved allowed model subset
- **AND** curated discovery runs again
- **THEN** the curated inventory is refreshed
- **AND** the allowed subset is not silently expanded beyond the operator-approved models

### Requirement: Native discovery parsing rejects non-model text
The system SHALL reject prose, Markdown headings, tables, bullets without valid model IDs, and error text from native model discovery output before persisting discovered Worker model IDs.

#### Scenario: AI prose is not persisted as model inventory
- **WHEN** a model discovery command exits successfully but stdout contains prose such as `Here's the model landscape in this codebase`
- **THEN** the system SHALL NOT persist that prose line as a discovered Worker model
- **AND** the Worker Setup UI SHALL NOT render that prose line as an allowed-model checkbox

#### Scenario: OpenCode line model output remains supported
- **WHEN** OpenCode native discovery emits plain lines containing valid model IDs
- **THEN** the system SHALL persist those model IDs as discovered OpenCode Worker models
- **AND** the parser SHALL NOT require JSON output for OpenCode discovery
