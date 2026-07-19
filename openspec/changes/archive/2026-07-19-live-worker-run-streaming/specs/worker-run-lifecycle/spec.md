## ADDED Requirements

### Requirement: Streamed capture preserves accounting and lifecycle transitions

The system SHALL derive the authoritative Worker execution token total and the task lifecycle
transition from the same final run evidence regardless of whether timeline events were captured
incrementally during execution. Incremental streamed capture SHALL NOT alter the final token total
or the lifecycle transition.

#### Scenario: Streamed and non-streamed runs finalize identically

- **WHEN** two Worker Runs produce identical adapter output, one captured incrementally and one not
- **THEN** both persist the same authoritative Worker execution token total
- **AND** both make the same lifecycle transition (Running→Review on success, retryable failure→Estimated)

#### Scenario: Malformed streamed line does not change finalization

- **WHEN** a Worker Run's streamed output contains lines that cannot be parsed as events
- **THEN** the final token total and the lifecycle transition are unchanged from the non-streamed outcome
