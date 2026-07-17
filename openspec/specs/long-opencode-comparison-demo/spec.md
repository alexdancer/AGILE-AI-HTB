# long-opencode-comparison-demo Specification

## Purpose
Define the standalone synthetic OpenCode comparison demo artifact and runbooks used to compare direct OpenCode execution with Foreman AI HQ-governed OpenCode execution while preserving obviously fake data and separated budget evidence.

## Requirements

### Requirement: Long synthetic OpenCode comparison task artifact
The system SHALL include a standalone markdown coding task artifact for comparing direct OpenCode execution with Foreman AI HQ-launched OpenCode execution.

#### Scenario: Task artifact exists
- **WHEN** an operator looks for the long OpenCode comparison task
- **THEN** the repository exposes a markdown artifact with a clear DEMO 2099 banner, a bounded Python CLI project goal, acceptance criteria, and instructions suitable for direct OpenCode or markdown task intake

#### Scenario: Task exercises multi-step coding work
- **WHEN** a Worker follows the long comparison task
- **THEN** the task requires planning, implementation, tests, debugging, and documentation for a local Python CLI project rather than only summarizing a large context file

### Requirement: Synthetic incident-ledger CLI scope
The long comparison task SHALL define a local-only Python CLI project named `incident-ledger` with enough complexity to produce meaningful Worker token usage while remaining feasible for a demo run.

#### Scenario: Required CLI capabilities are specified
- **WHEN** the task artifact describes the target project
- **THEN** it includes commands for ingesting incidents, listing records, deduplicating similar incidents, scoring severity, generating reports, and exporting data

#### Scenario: Required implementation constraints are specified
- **WHEN** the task artifact describes implementation requirements
- **THEN** it requires JSONL and markdown input parsing, SQLite persistence, deterministic duplicate detection, weighted severity scoring, Markdown and JSON reports, pytest coverage, and README usage examples

### Requirement: Demo data remains obviously synthetic
The long comparison task and related demo fixtures SHALL contain only obviously synthetic data and SHALL forbid real external API calls or real customer data.

#### Scenario: Synthetic marker requirements are present
- **WHEN** the task artifact provides sample records, addresses, emails, accounts, dates, or identifiers
- **THEN** those examples use DEMO markers, 2099 dates, `.invalid` emails, fake addresses containing DEMO, and 999-style account numbers or IDs

#### Scenario: Real external calls are forbidden
- **WHEN** the task artifact describes integrations or exports
- **THEN** it explicitly forbids real network calls, real external APIs, real GitHub/Gist calls, and real customer or incident data

### Requirement: Direct OpenCode baseline runbook
The system SHALL include runbook instructions for running the long task directly with OpenCode and preserving native usage evidence as the uncontrolled baseline.

#### Scenario: Direct baseline captures usage
- **WHEN** an operator runs the comparison baseline
- **THEN** the runbook instructs them to use OpenCode's machine-readable output mode where available and save the command output containing token usage evidence

#### Scenario: Direct baseline is not treated as harness-governed spend
- **WHEN** the operator compares direct OpenCode usage to Foreman AI HQ usage
- **THEN** the runbook labels direct OpenCode usage as external baseline evidence, not Foreman AI HQ Worker execution spend

### Requirement: Foreman AI HQ comparison runbook
The system SHALL include runbook instructions for submitting or launching the same long task through Foreman AI HQ with a separately configured Worker budget.

#### Scenario: Harness run uses existing OpenCode adapter semantics
- **WHEN** the operator runs the task through Foreman AI HQ
- **THEN** the runbook uses the OpenCode Worker Adapter identity and a verified tracking mode such as `native_usage` or `proxy_governed`, without introducing a generic provider-key adapter

#### Scenario: Harness run compares budgeted behavior
- **WHEN** the operator runs the task through Foreman AI HQ
- **THEN** the runbook instructs them to configure a Worker budget that may differ from the direct OpenCode baseline and compare launch blocks, overrides, alarms, Worker Run evidence, and session report usage

### Requirement: Fake-data invariant coverage
The system SHALL include automated invariant coverage that scans the long comparison demo artifacts for obviously synthetic data and forbidden real-world integration instructions.

#### Scenario: Demo artifact invariant test passes
- **WHEN** the test suite runs the long comparison demo fake-data invariant checks
- **THEN** the tests verify the expected DEMO/2099/.invalid/999-style markers and fail if the artifact contains real-looking data or instructions to call real external services

### Requirement: Harness comparison writes to harness target
The long OpenCode comparison demo SHALL prove that harness-launched Worker changes land in `.demo/opencode-comparison/harness-target` and remain isolated from the direct baseline target and repository root.

#### Scenario: Harness target receives generated project
- **WHEN** the long OpenCode comparison task is launched through Foreman AI HQ with the OpenCode Worker Adapter configured to `.demo/opencode-comparison/harness-target`
- **THEN** generated project files such as `pyproject.toml`, `README.md`, `src/incident_ledger/`, `tests/`, and `examples/` appear under `.demo/opencode-comparison/harness-target`
- **AND** the evidence does not rely on files under repository-level `incident-ledger/` as the harness result

#### Scenario: Demo detects misplaced harness output
- **WHEN** OpenCode native usage evidence exists but generated files appear outside `.demo/opencode-comparison/harness-target`
- **THEN** the demo evidence SHALL identify this as a workdir mismatch
- **AND** the runbook SHALL direct the operator to treat it as a launch configuration failure, not as a successful harness comparison
