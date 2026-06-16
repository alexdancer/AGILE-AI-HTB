## ADDED Requirements

### Requirement: Budgets gate launches
The system SHALL evaluate remaining budget before launching Worker Sessions and block normal launch when the estimate exceeds remaining budget.

#### Scenario: Estimate fits remaining budget
- **WHEN** a Task estimate is within remaining budget and other Launch Guardrails pass
- **THEN** the Portal allows normal launch

#### Scenario: Estimate exceeds remaining budget
- **WHEN** a Task estimate exceeds remaining budget before launch
- **THEN** the Portal blocks normal launch and offers an explicit budget override flow

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
