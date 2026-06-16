# budgeted-launch-control Specification

## Purpose
Define how the harness gates Worker Session launches against available budget, records explicit override approvals, categorizes spend, and preserves operator control for overruns or manual aborts.

## Requirements

### Requirement: Budgets gate launches
The system SHALL evaluate remaining budget before launching Worker Sessions and block normal launch when the estimate exceeds remaining budget, using spend categories that distinguish control-plane, Worker execution, and verification/overhead usage.

#### Scenario: Estimate fits remaining budget
- **WHEN** a Task estimate is within remaining Worker execution budget and other Launch Guardrails pass
- **THEN** the Portal allows normal launch

#### Scenario: Estimate exceeds remaining budget
- **WHEN** a Task estimate exceeds remaining Worker execution budget before launch
- **THEN** the Portal blocks normal launch and offers an explicit budget override flow

#### Scenario: Control-plane spend shown separately
- **WHEN** AGILE-AI-HTB uses its own model for estimation, planning, recommendation, or reporting
- **THEN** the token ledger and budget UI classify that usage separately from Worker execution spend

### Requirement: Explicit budget override
The system SHALL require explicit User approval to launch a Task whose estimate exceeds remaining budget.

#### Scenario: User approves budget override
- **WHEN** the User confirms Launch with budget override
- **THEN** the system records `budget_override=true`, audits the approval, and allows launch if other Launch Guardrails pass

### Requirement: Running sessions are not auto-killed for budget overrun
The system SHALL allow running Worker Sessions to finish when actual usage exceeds estimate or budget.

#### Scenario: Running session overruns budget
- **WHEN** a running Worker Session exceeds estimate or budget
- **THEN** the system records the overrun, raises alarms, and does not automatically terminate the Worker

### Requirement: Manual abort remains available
The system SHALL allow a User or admin to manually abort a running Worker Session.

#### Scenario: User aborts running session
- **WHEN** the User or admin manually aborts a running Worker Session
- **THEN** the runner stops the Worker process and preserves session logs, token ledger entries, and failure/abort reason

### Requirement: Budget-authoritative tracking required for governed launch
The system SHALL require proxy-governed or native-usage verified tracking before treating a Worker launch as budget-authoritative.

#### Scenario: Proxy-governed usage counts toward Worker budget
- **WHEN** a Worker Session records usage through the Harness Proxy
- **THEN** the system counts that usage against Worker execution budget with source `proxy_governed`

#### Scenario: Native usage counts toward Worker budget
- **WHEN** a Worker Session imports trustworthy usage from the native Worker Harness
- **THEN** the system counts that usage against Worker execution budget with source `native_usage`

#### Scenario: Observed-only usage is not budget-authoritative
- **WHEN** a Worker Session can be launched but cannot provide proxy-governed or native usage evidence
- **THEN** the system does not count the session as normal governed execution and labels any token estimate as non-authoritative
