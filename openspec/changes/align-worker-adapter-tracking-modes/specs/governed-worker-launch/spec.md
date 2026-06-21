## ADDED Requirements

### Requirement: Worker Adapter tracking modes govern launchability
The system SHALL treat Worker Adapters as local coding-agent CLI integrations and SHALL separately verify how token usage is proven for each adapter launch.

#### Scenario: Proxy-governed adapter is launchable with proxy evidence
- **WHEN** a Worker Adapter has `proxy_governed` tracking mode
- **AND** Harness Proxy token rows have been verified for the selected model
- **AND** Harness Proxy URL and session API key wiring are present
- **THEN** the adapter is eligible for governed AGILE Board launch if all other Launch Guardrails pass

#### Scenario: Native usage adapter is launchable without proxy wiring
- **WHEN** a Worker Adapter has `native_usage` tracking mode
- **AND** trustworthy native usage evidence has been verified for the selected model
- **THEN** the adapter is eligible for governed AGILE Board launch without requiring Harness Proxy URL or session API key wiring

#### Scenario: Observed-only adapter is not board-launchable
- **WHEN** a Worker Adapter has `observed_only` tracking mode
- **THEN** the normal AGILE Board SHALL NOT launch it for a Task

### Requirement: Native usage is accounting-governed but not runtime request-governed
The system SHALL distinguish native usage accounting authority from proxy runtime request governance.

#### Scenario: Native usage launch does not claim request governance
- **WHEN** a Worker Run uses `native_usage` tracking mode
- **THEN** the system records it as budget-authoritative only through launch/review governance, preflight budget checks, post-run reconciliation, evidence review, and alarms after usage is known
- **AND** the system SHALL NOT label the run as runtime request-governed

#### Scenario: Proxy-governed launch supports runtime request guardrails
- **WHEN** a Worker Run uses `proxy_governed` tracking mode
- **THEN** runtime request guardrails may apply while Worker model calls pass through the Harness Proxy

### Requirement: Native usage budget override acknowledgement
The system SHALL require explicit native-usage acknowledgement when a budget override is used for a native usage launch.

#### Scenario: Native usage override records acknowledgement
- **WHEN** a Task estimate exceeds the remaining daily Worker budget
- **AND** the selected Worker Adapter uses `native_usage` tracking mode
- **AND** the operator chooses Launch with budget override
- **THEN** the operator must acknowledge that native usage cannot be request-throttled mid-run
- **AND** the Worker Run records `budget_override=true` and the acknowledgement for audit
- **AND** post-run reconciliation may report an overrun after native usage evidence is imported
