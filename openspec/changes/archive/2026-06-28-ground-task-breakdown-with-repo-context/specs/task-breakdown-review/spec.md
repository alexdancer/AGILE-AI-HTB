## ADDED Requirements

### Requirement: Connected-project breakdown uses Repo Context Brief
The Task Breakdown Agent SHALL receive bounded Repo Context Brief information when creating a Proposed Task Breakdown for connected-project intake with a readable project root.

#### Scenario: Project markdown breakdown includes repo context
- **WHEN** an operator submits Markdown upload or Markdown paste from a connected project board
- **AND** the connected project root can be read
- **THEN** the Task Breakdown Agent request includes bounded repo context with available repo instructions, manifests, likely entry points, detected verification commands, and a repository file sample
- **AND** the original source text remains a separate field from the repo context

#### Scenario: Oversized project task breakdown includes repo context
- **WHEN** an operator submits an oversized task from a connected project board that requires Task Breakdown review
- **AND** the connected project root can be read
- **THEN** the Task Breakdown Agent request includes bounded repo context before proposing implementation and Acceptance Verification candidates

#### Scenario: Global breakdown stays unchanged
- **WHEN** an operator submits Markdown or oversized task intake outside a connected project
- **THEN** the Task Breakdown Agent request does not include project repo context
- **AND** Task Breakdown review proceeds with the existing source text, intake metadata, and structure hints

### Requirement: Breakdown review preserves repo-context evidence
The system SHALL preserve bounded repo-context evidence on Proposed Task Breakdown records when repo context is supplied to the Task Breakdown Agent.

#### Scenario: Review record shows context source summary
- **WHEN** a Proposed Task Breakdown is created with Repo Context Brief input
- **THEN** the review record stores bounded repo-context metadata showing the context source list or summary
- **AND** the stored evidence does not include secret-named files or unredacted secret patterns

#### Scenario: Repo context failure does not block manual recovery
- **WHEN** a connected project root is unavailable, unreadable, or otherwise fails while building repo context for Task Breakdown
- **THEN** the system creates or retries the Proposed Task Breakdown without repo context
- **AND** it does not create AGILE Board Tasks without the normal operator acceptance step
