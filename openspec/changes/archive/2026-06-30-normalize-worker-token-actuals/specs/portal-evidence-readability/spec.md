## MODIFIED Requirements

### Requirement: Session reports explain native token components
Session and Worker report surfaces SHALL show normalized Worker actuals, cache-read/reused-context evidence, provider raw totals, cost, and recognizable token component evidence before raw usage JSON when Worker/native usage contains cache, fresh input, output, reasoning, or cost details.

#### Scenario: Worker report has Claude Code cache evidence
- **WHEN** an operator opens a Worker session or report whose raw usage contains Claude-style `input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, or `output_tokens`
- **THEN** the report SHALL show normalized Worker actual tokens excluding `cache_read_input_tokens`
- **AND** the report SHALL count `cache_creation_input_tokens` as cache write/create in normalized Worker actuals
- **AND** the report SHALL show provider raw total tokens and cost when available
- **AND** the report SHALL show a component summary that labels fresh input, cache read/reused context, cache write/create, output, and cost when available
- **AND** the raw usage JSON SHALL remain available behind the existing raw evidence disclosure pattern

#### Scenario: Worker report has OpenCode cache evidence
- **WHEN** an operator opens a Worker session or report whose raw usage contains OpenCode-style `tokens.cache.read`, `tokens.cache.write`, `tokens.input`, `tokens.output`, or `tokens.reasoning`
- **THEN** the report SHALL show normalized Worker actual tokens excluding `tokens.cache.read`
- **AND** the report SHALL count `tokens.cache.write`, `tokens.input`, `tokens.output`, and `tokens.reasoning` in normalized Worker actuals when present
- **AND** the report SHALL show cache read/write, fresh input, output, reasoning, provider raw total, and cost components when available
- **AND** the report SHALL keep raw usage evidence secondary and auditable

#### Scenario: Worker report has Codex or OpenAI cached input evidence
- **WHEN** an operator opens a Worker session or report whose raw usage contains Codex/OpenAI-style cached input fields such as `cached_input_tokens`, `cached_tokens`, `input_token_details.cached_tokens`, or `prompt_tokens_details.cached_tokens`
- **THEN** the report SHALL show cached input as cache read/reused context excluded from normalized Worker actuals
- **AND** the report SHALL show unavailable cache write/create rather than inventing a value when the provider does not expose one

### Requirement: Session reports keep token totals honest when components are partial
Session and Worker report surfaces SHALL preserve provider/ledger raw total tokens as audit evidence when normalized components are partial, missing, or do not sum exactly to the reported total, while using normalized Worker actuals for task-actual and budget comparison labels when component evidence supports that calculation.

#### Scenario: Component sum differs from provider total
- **WHEN** a Worker report has recognized token components whose sum differs from the ledger or provider total
- **THEN** the report SHALL show normalized Worker actuals and provider raw total as distinct labeled values
- **AND** the report SHALL label any remaining difference as unclassified or provider-total-only evidence when displayed
- **AND** the report SHALL NOT silently replace raw provider evidence with a recomputed partial total
- **AND** the report SHALL NOT treat cache-read/reused-context tokens as fresh task text
