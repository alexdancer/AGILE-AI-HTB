# governance-integration-smoke Specification

## Purpose

Define the synthetic service-level integration coverage that proves the local governance loop without a browser, external provider, or Worker dependency.

## Requirements

### Requirement: Governance integration smoke test proves the governance loop

The test suite SHALL include a service-level pytest smoke test that exercises the full governance loop: project connection → task creation → Worker launch simulation → token turn recording → task transition to Review. The test SHALL use only synthetic data and SHALL NOT require a browser, network access, real Worker CLI installations, or provider API keys. This test SHALL be identified as a Governance Integration Smoke Test rather than a Portal E2E Test.

#### Scenario: Full governance loop completes

- **WHEN** a connected project exists with a launch-ready worker adapter
- **AND** a task is created with an estimate
- **AND** the task is launched (simulated Worker Run)
- **AND** token usage is recorded
- **AND** the task is refreshed from its session
- **THEN** the task SHALL be in Review status
- **AND** a Worker Run record SHALL exist for the task
- **AND** token turns SHALL be recorded for the session

#### Scenario: Smoke test runs in CI without external dependencies

- **WHEN** the smoke test is executed via `pytest`
- **THEN** no network requests SHALL be made
- **AND** no subprocess SHALL be spawned to a real Worker CLI
- **AND** the test SHALL pass using only in-memory/synthetic data
