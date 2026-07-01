## ADDED Requirements

### Requirement: Breakdown-created implementation prompts use minimal slice context
The system SHALL shape Worker prompts for accepted implementation candidates from a Proposed Task Breakdown using the smallest honest slice context that preserves the task objective, hard constraints, slice-specific acceptance checks, required verification, and a compact global contract summary. The system SHALL NOT repeat unrelated source prose, sibling task details, stale setup text, or raw evidence into every implementation prompt when a compact reference is sufficient.

#### Scenario: Implementation candidate receives ponytail-shaped prompt
- **WHEN** the operator accepts an `implementation` candidate from a Proposed Task Breakdown
- **THEN** the accepted Task sent to Task Estimation and Worker launch context SHALL include the candidate objective or implementation prompt
- **AND** it SHALL include hard global constraints and relevant candidate-scoped acceptance criteria
- **AND** it SHALL include the editable global contract summary in compact form
- **AND** it SHALL omit unrelated sibling candidate details and unnecessary raw source prose from the implementation prompt

#### Scenario: Required guardrails are preserved
- **WHEN** prompt shaping removes repeated or unrelated prose from an implementation candidate
- **THEN** the prompt SHALL still preserve security constraints, no-secret/no-network constraints, synthetic-data rules, required verification commands, expected final response shape, and any acceptance criteria relevant to that candidate

#### Scenario: Acceptance verification keeps enough source contract
- **WHEN** the operator accepts an `acceptance_verification` candidate
- **THEN** the accepted Task SHALL keep the global contract summary and the full original source contract needed to verify the combined artifact
- **AND** prompt shaping SHALL NOT reduce Acceptance Verification into a narrow implementation-slice prompt
