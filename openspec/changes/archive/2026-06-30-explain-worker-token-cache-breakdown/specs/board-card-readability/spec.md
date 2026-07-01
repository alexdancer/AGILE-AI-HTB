## ADDED Requirements

### Requirement: Board cards explain Worker actual token components
Board task cards SHALL provide a compact explanation of actual Worker execution token composition when authoritative component evidence exists for the task's Worker Run.

#### Scenario: Review card has cache-heavy actual tokens
- **WHEN** a task is in Review after a successful Worker Run
- **AND** `task.actual_tokens` is populated from Worker execution evidence
- **AND** raw usage evidence contains recognizable fresh input, cache read, cache write/create, output, reasoning, or cost components
- **THEN** the board card SHALL keep the actual Worker token total visible in the compact metadata
- **AND** the card SHALL provide a concise cache/fresh/output explanation in compact metadata or an immediately adjacent disclosure
- **AND** the card SHALL NOT merge Agent Review, estimation, task breakdown, or other control-plane spend into the task actual token value

#### Scenario: Done card preserves token component explanation
- **WHEN** an operator marks a reviewed task Done
- **AND** actual Worker token component evidence exists for that task
- **THEN** the Done card SHALL continue to show the actual Worker token total
- **AND** the Done card SHALL keep the component explanation available without requiring raw JSON inspection

#### Scenario: Actual token components are unavailable
- **WHEN** a task has `actual_tokens` but no recognizable token component evidence
- **THEN** the board card SHALL show the actual Worker token total
- **AND** the card SHALL NOT fabricate fresh input, cache, output, reasoning, or cost component values
