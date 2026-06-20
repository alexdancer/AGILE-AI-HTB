## ADDED Requirements

### Requirement: Model-backed demo worker timeout is configurable
The local execution backend SHALL allow Worker subprocess timeout to be configured per adapter or command plan so model-backed demo workers can run through real provider latency without changing the global timeout for every Worker command.

#### Scenario: Demo worker uses extended timeout
- **WHEN** the demo Worker adapter launches a model-backed task through the Harness Proxy
- **THEN** the command plan includes an explicit timeout suitable for multiple real model calls
- **AND** the subprocess runner uses that timeout instead of the global default

#### Scenario: Generic worker keeps safe default timeout
- **WHEN** a Worker adapter does not specify a launch timeout
- **THEN** the subprocess runner uses the existing safe default timeout

### Requirement: Local execution preserves model layer separation
The local execution backend SHALL keep control-plane model usage for estimation, planning, recommendation, summaries, and reports separate from Worker Harness model usage during local launches.

#### Scenario: Estimator works but worker launch fails
- **WHEN** the control-plane estimator successfully creates Estimated tasks
- **AND** a later Worker launch fails operationally
- **THEN** the failure is attributed to the Worker/local execution layer
- **AND** the system does not imply that the control-plane model connection failed
