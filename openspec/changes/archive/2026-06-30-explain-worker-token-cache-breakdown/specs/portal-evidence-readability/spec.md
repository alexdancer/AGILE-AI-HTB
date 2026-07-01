## ADDED Requirements

### Requirement: Session reports explain native token components
Session and Worker report surfaces SHALL show recognizable token component evidence before raw usage JSON when Worker/native usage contains cache, fresh input, output, reasoning, or cost details.

#### Scenario: Worker report has Claude Code cache evidence
- **WHEN** an operator opens a Worker session or report whose raw usage contains Claude-style `input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, or `output_tokens`
- **THEN** the report SHALL show the authoritative Worker token total
- **AND** the report SHALL show a component summary that labels fresh input, cache read/reused context, cache write/create, output, and cost when available
- **AND** the raw usage JSON SHALL remain available behind the existing raw evidence disclosure pattern

#### Scenario: Worker report has OpenCode cache evidence
- **WHEN** an operator opens a Worker session or report whose raw usage contains OpenCode-style `tokens.cache.read`, `tokens.cache.write`, `tokens.input`, `tokens.output`, or `tokens.reasoning`
- **THEN** the report SHALL show the authoritative Worker token total
- **AND** the report SHALL show cache read/write, fresh input, output, reasoning, and cost components when available
- **AND** the report SHALL keep raw usage evidence secondary and auditable

#### Scenario: Worker report has Codex or OpenAI cached input evidence
- **WHEN** an operator opens a Worker session or report whose raw usage contains Codex/OpenAI-style cached input fields such as `cached_input_tokens`, `cached_tokens`, `input_token_details.cached_tokens`, or `prompt_tokens_details.cached_tokens`
- **THEN** the report SHALL show cached input as cache read/reused context
- **AND** the report SHALL show unavailable cache write/create rather than inventing a value when the provider does not expose one

### Requirement: Session reports keep token totals honest when components are partial
Session and Worker report surfaces SHALL preserve provider/ledger total tokens as authoritative when normalized components are partial, missing, or do not sum exactly to the reported total.

#### Scenario: Component sum differs from provider total
- **WHEN** a Worker report has recognized token components whose sum differs from the ledger or provider total
- **THEN** the report SHALL show the ledger/provider total as authoritative
- **AND** the report SHALL label any remaining difference as unclassified or provider-total-only evidence when displayed
- **AND** the report SHALL NOT silently replace the authoritative total with a recomputed partial total
