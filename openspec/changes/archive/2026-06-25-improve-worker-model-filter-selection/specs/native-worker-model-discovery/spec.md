## ADDED Requirements

### Requirement: Allowed model bulk selection preserves discovery boundary
The system SHALL apply Worker Setup bulk allowed-model selection only to model IDs from the adapter's discovered Worker model inventory, and SHALL continue rejecting submitted allowed model IDs that were not discovered for that adapter.

#### Scenario: Visible bulk selection submits discovered models
- **WHEN** model discovery has returned models for a Worker Adapter
- **AND** the operator filters the discovered list and uses visible bulk selection
- **THEN** the saved allowed model subset contains only selected discovered model IDs
- **AND** the full discovered inventory remains preserved separately from the allowed subset

#### Scenario: Invalid allowed model still rejected
- **WHEN** a request submits an allowed model ID that is not in the adapter's discovered model inventory
- **THEN** the system rejects the request before changing the adapter's allowed model subset
