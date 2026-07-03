## ADDED Requirements

### Requirement: Task Breakdown request scale is explicit
The system SHALL keep Task Breakdown Model request sizing explicit and scoped to Task Breakdown Agent calls so operators can distinguish reachability checks from full structured breakdown generation.

#### Scenario: Task Breakdown uses explicit output budget
- **WHEN** the Task Breakdown Agent calls a configured Task Breakdown Model
- **THEN** the request SHALL use an explicit max output token budget scoped to Task Breakdown Agent work
- **AND** the output budget SHALL NOT change unrelated control-plane connection tests, task estimation requests, Worker Adapter launches, or Worker model selection

#### Scenario: Task Breakdown timeout is explicit
- **WHEN** the Task Breakdown Agent calls a configured Task Breakdown Model
- **THEN** the provider request timeout used for that call SHALL be explicit in configuration or code
- **AND** timeout diagnostics SHALL report that timeout value without exposing secrets or source text

#### Scenario: Reachability test remains small
- **WHEN** the operator runs the Control Plane connection test
- **THEN** the test SHALL remain a small provider reachability check
- **AND** the system SHALL NOT treat successful reachability evidence as proof that large Task Breakdown structured-output requests will complete within their timeout budget
