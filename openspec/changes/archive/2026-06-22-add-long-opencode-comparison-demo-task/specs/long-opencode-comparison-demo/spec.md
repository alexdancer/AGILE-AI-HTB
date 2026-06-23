## ADDED Requirements

### Requirement: Long synthetic OpenCode comparison task artifact
The system SHALL include a standalone markdown coding task artifact for comparing direct OpenCode execution with AGILE-AI-HTB-launched OpenCode execution.

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
- **WHEN** the operator compares direct OpenCode usage to AGILE-AI-HTB usage
- **THEN** the runbook labels direct OpenCode usage as external baseline evidence, not AGILE-AI-HTB Worker execution spend

### Requirement: AGILE-AI-HTB comparison runbook
The system SHALL include runbook instructions for submitting or launching the same long task through AGILE-AI-HTB with a separately configured Worker budget.

#### Scenario: Harness run uses existing OpenCode adapter semantics
- **WHEN** the operator runs the task through AGILE-AI-HTB
- **THEN** the runbook uses the OpenCode Worker Adapter identity and a verified tracking mode such as `native_usage` or `proxy_governed`, without introducing a generic provider-key adapter

#### Scenario: Harness run compares budgeted behavior
- **WHEN** the operator runs the task through AGILE-AI-HTB
- **THEN** the runbook instructs them to configure a Worker budget that may differ from the direct OpenCode baseline and compare launch blocks, overrides, alarms, Worker Run evidence, and session report usage

### Requirement: Fake-data invariant coverage
The system SHALL include automated invariant coverage that scans the long comparison demo artifacts for obviously synthetic data and forbidden real-world integration instructions.

#### Scenario: Demo artifact invariant test passes
- **WHEN** the test suite runs the long comparison demo fake-data invariant checks
- **THEN** the tests verify the expected DEMO/2099/.invalid/999-style markers and fail if the artifact contains real-looking data or instructions to call real external services
