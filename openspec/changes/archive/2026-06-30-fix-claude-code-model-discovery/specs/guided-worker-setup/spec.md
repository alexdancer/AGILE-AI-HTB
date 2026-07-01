## ADDED Requirements

### Requirement: Worker Setup actions preserve active adapter context
Worker Setup SHALL return the operator to the adapter they acted on after adapter-scoped POST actions.

#### Scenario: Discovery returns to selected adapter
- **WHEN** an operator selects Claude Code on `/settings/workers`
- **AND** submits model discovery for Claude Code
- **THEN** the response SHALL return to `/settings/workers?adapter_id=claude_code`
- **AND** the guided setup workflow SHALL show Claude Code as the active adapter

#### Scenario: Allowed-model save returns to selected adapter
- **WHEN** an operator saves allowed models for a non-default Worker Adapter
- **THEN** the response SHALL return to `/settings/workers?adapter_id={adapter_id}` for that adapter
- **AND** the page SHALL NOT fall back to rendering another default adapter as if it were the target of the action

#### Scenario: Verification returns to selected adapter
- **WHEN** an operator verifies tracking for a Worker Adapter
- **THEN** the response SHALL return to `/settings/workers?adapter_id={adapter_id}` for that adapter
- **AND** verification status and model inventory shown in the guided workflow SHALL correspond to that adapter
