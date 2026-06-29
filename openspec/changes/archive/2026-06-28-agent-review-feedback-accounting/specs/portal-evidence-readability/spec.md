## MODIFIED Requirements

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
