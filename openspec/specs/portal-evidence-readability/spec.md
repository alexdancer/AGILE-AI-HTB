# portal-evidence-readability Specification

## Purpose

Define how Portal session and report surfaces summarize governance evidence first while preserving raw logs, timeline payloads, and diagnostics for audit.
## Requirements
### Requirement: Session evidence summary appears before raw evidence
Session and report surfaces SHALL show concise, bounded evidence summaries before raw logs, timeline payloads, stdout, stderr, full task text, review findings, or diagnostic details. Agent Review sessions SHALL be recognizable as control-plane review sessions with model, status, and token totals before raw details.

#### Scenario: Sessions index shows compact rows
- **WHEN** an operator opens the sessions index
- **THEN** each session row SHALL show a compact task/session summary instead of unbounded full task text
- **AND** the row SHALL preserve key scan fields including session link, model, status, token totals, evidence counts, zone, and alarm count
- **AND** Agent Review sessions SHALL be distinguishable from Worker execution sessions by their task/session summary or evidence label

#### Scenario: Session report starts with launch evidence summary
- **WHEN** an operator opens a completed session or Worker Run report surface
- **THEN** the page SHALL show a bounded summary of task, selected project when known, Worker Adapter, Worker model, tracking mode, status/result, token usage, alarms, and review state when available
- **AND** raw evidence and full text SHALL remain available after the summary

#### Scenario: Agent Review session report starts with review evidence
- **WHEN** an operator opens an Agent Review session report
- **THEN** the page SHALL show a bounded summary of the reviewed task, control-plane review model, review status, recommendation or failure state, and Agent Review token usage
- **AND** raw review findings and prompt context SHALL remain secondary

#### Scenario: Missing evidence is explicit
- **WHEN** a session or Worker Run lacks authoritative token usage, review evidence, or launch metadata
- **THEN** the summary SHALL identify the missing evidence instead of silently omitting the field

### Requirement: Raw evidence remains auditable but secondary
The Portal SHALL preserve access to raw governance evidence while defaulting to human-readable summaries and bounded preview regions.

#### Scenario: Raw logs are disclosed on demand
- **WHEN** stdout, stderr, command evidence, Worker timeline entries, full task text, raw repo context brief text, or Agent Review findings are available
- **THEN** the Portal SHALL render them behind native disclosure or equivalent secondary sections unless they are the primary error message

#### Scenario: Long raw evidence stays bounded when opened
- **WHEN** an operator expands raw repo context, long command evidence, timeline details, stdout, stderr, or full task/report text
- **THEN** the Portal SHALL render the content in a bounded or wrapping region that does not make the page unusable while scrolling

#### Scenario: Error evidence stays visible enough to act
- **WHEN** a Worker launch or review fails
- **THEN** the Portal SHALL show a concise failure reason and next action before any raw stderr or diagnostic payload

### Requirement: Session report shows related Agent Review results
A Worker session report SHALL surface the latest Agent Review result from the task linked to that session when review metadata exists, before raw evidence sections.

#### Scenario: Worker session has completed Agent Review
- **WHEN** an operator opens a Worker session report
- **AND** a task linked to that session has completed Agent Review metadata
- **THEN** the report SHALL show an Agent Review results section with status, recommendation, summary, control-plane model, reviewed timestamp when available, review session link when available, and review token total when available
- **AND** the report SHALL keep detailed findings available in bounded or expandable evidence sections

#### Scenario: Worker session has failed Agent Review
- **WHEN** an operator opens a Worker session report
- **AND** a task linked to that session has failed Agent Review metadata
- **THEN** the report SHALL show the Agent Review failure status and sanitized failure evidence
- **AND** the report SHALL keep the Worker session evidence visible and unchanged

#### Scenario: Worker session has no Agent Review
- **WHEN** an operator opens a Worker session report
- **AND** no linked task has Agent Review metadata
- **THEN** the report SHALL not fabricate review results or zero review tokens

### Requirement: Review tokens remain separate from Worker execution totals
Session report review-result display SHALL show Agent Review token totals as control-plane/reporting evidence and SHALL NOT merge those tokens into Worker execution actuals.

#### Scenario: Review tokens are displayed separately
- **WHEN** a Worker session report shows related Agent Review metadata with token totals
- **THEN** the review token total SHALL be labeled as review/control-plane usage
- **AND** the Worker session token totals SHALL remain based on that Worker session's token log
- **AND** task actual Worker tokens SHALL remain unchanged

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
