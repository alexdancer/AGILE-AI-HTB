## ADDED Requirements

### Requirement: Worker Setup distinguishes Codex verification authority
Worker Setup SHALL present Codex verification and readiness according to the selected tracking mode's authority, not just whether a sentinel command returned text.

#### Scenario: Codex native usage is launch-ready after authoritative verification
- **WHEN** the active Worker Adapter is Codex
- **AND** Codex has at least one operator-approved allowed model
- **AND** Codex has passed `native_usage` verification with `tracking_authoritative=true`
- **THEN** Worker Setup SHALL show Codex as launch-ready for normal governed AGILE Board tasks
- **AND** the readiness summary SHALL identify the mode as native usage tracking rather than Harness Proxy request governance

#### Scenario: Codex observed-only success is not launch-ready
- **WHEN** the active Worker Adapter is Codex
- **AND** the latest Codex verification evidence is `observed_only` or `tracking_authoritative=false`
- **THEN** Worker Setup SHALL show the result as diagnostic-only
- **AND** the readiness summary SHALL keep normal governed launch unavailable
- **AND** the next action SHALL direct the operator to run or fix native usage verification

#### Scenario: Codex setup shows exact curated model choices
- **WHEN** Worker Setup renders Codex model choices after curated discovery
- **THEN** the selectable Codex model IDs SHALL be `gpt-5.4` and `gpt-5.4-mini`
- **AND** stale placeholder IDs SHALL NOT appear as curated Codex choices
