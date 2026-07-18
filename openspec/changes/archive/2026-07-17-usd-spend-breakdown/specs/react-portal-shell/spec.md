## ADDED Requirements

### Requirement: React dashboard JSON bounds USD spend fields

The authenticated React dashboard JSON handoff SHALL project the coverage-aware USD spend fields
for the budget spend breakdown as bounded values derived from the existing shared dashboard
calculation, without exposing raw evidence. These fields are additive to the existing bounded
dashboard projection; the existing token and preview fields are unchanged.

#### Scenario: Cost-by-category uses the fixed category keys and bounded numbers

- **WHEN** an authenticated operator requests the React dashboard JSON
- **THEN** the response SHALL include a `cost_by_category` object whose keys are exactly the fixed spend categories `control_plane`, `task_breakdown`, `worker_execution`, `adapter_verification`, `reporting_summary`, and `other`
- **AND** each value SHALL be a finite non-negative JSON number, or `null` when that category has tracked tokens but no resolved cost

#### Scenario: Total cost and coverage are bounded

- **WHEN** an authenticated operator requests the React dashboard JSON
- **THEN** the response SHALL include `total_cost` as a finite non-negative JSON number, or `null` when no tracked spend has a resolved cost
- **AND** it SHALL include `priced_tokens` and `unpriced_tokens` as non-negative integers whose sum equals the total tracked governed token spend for the window

#### Scenario: USD fields never expose raw evidence

- **WHEN** the dashboard JSON projects the USD spend fields
- **THEN** it SHALL derive them from the shared dashboard/token-ledger calculation rather than a parallel computation
- **AND** it SHALL NOT include raw usage payloads, secret values, or per-turn records in the USD fields
