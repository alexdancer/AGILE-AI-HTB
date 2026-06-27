## MODIFIED Requirements

### Requirement: Session evidence summary appears before raw evidence
Session and report surfaces SHALL show concise, bounded evidence summaries before raw logs, timeline payloads, stdout, stderr, full task text, or diagnostic details.

#### Scenario: Sessions index shows compact rows
- **WHEN** an operator opens the sessions index
- **THEN** each session row SHALL show a compact task/session summary instead of unbounded full task text
- **AND** the row SHALL preserve key scan fields including session link, model, status, token totals, evidence counts, zone, and alarm count

#### Scenario: Session report starts with launch evidence summary
- **WHEN** an operator opens a completed session or Worker Run report surface
- **THEN** the page SHALL show a bounded summary of task, selected project when known, Worker Adapter, Worker model, tracking mode, status/result, token usage, alarms, and review state when available
- **AND** raw evidence and full text SHALL remain available after the summary

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
