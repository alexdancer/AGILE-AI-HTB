## ADDED Requirements

### Requirement: Needs You aggregates project decisions awaiting a human
The system SHALL provide a project-scoped Needs You queue that aggregates every item awaiting a human decision for the selected project: pending Proposed Task Breakdowns awaiting review, tasks flagged for a manual estimate, launches refused by Launch Guardrails, completed Worker Runs awaiting Review Disposition, and budget overrides awaiting approval. Needs You SHALL be a derived read-model over existing data and SHALL NOT introduce a new persisted lifecycle state.

#### Scenario: Needs You lists decisions with reason and action
- **WHEN** an authenticated operator loads Needs You for a project with a pending breakdown and a task flagged for manual estimate
- **THEN** each entry SHALL name its reason and the action that clears it
- **AND** entries SHALL be scoped to the selected project

#### Scenario: Empty Needs You renders a bounded empty state
- **WHEN** an authenticated operator loads Needs You for a project with no pending decisions
- **THEN** the surface SHALL render a concise empty state rather than an error or a fabricated item

### Requirement: Needs You is pinned on the Pipeline Surface with a navigation badge
The Needs You queue SHALL appear as a section pinned at the top of the Pipeline Surface, and project navigation SHALL show a live count badge so the queue stays reachable from the Execution Floor.

#### Scenario: Pipeline shows Needs You first
- **WHEN** an authenticated operator opens the Pipeline Surface with one or more pending decisions
- **THEN** Needs You SHALL render above task intake
- **AND** navigation SHALL show a count badge matching the number of pending decisions

#### Scenario: Badge reachable from the Floor
- **WHEN** an authenticated operator is on the Execution Floor with pending decisions
- **THEN** navigation SHALL show the Needs You count badge linking back to the Pipeline Surface Needs You section

### Requirement: Needs You is distinct from Alarms
Needs You SHALL represent decisions blocking forward progress and SHALL remain separate from Alarms, which represent runtime behavioral warnings about an already-running Worker. The system SHALL NOT merge the two surfaces.

#### Scenario: Runtime alarm does not appear in Needs You
- **WHEN** a running Worker triggers a budget-burn or loop Alarm
- **THEN** that Alarm SHALL appear in the Alarms surface
- **AND** it SHALL NOT be listed as a Needs You decision item
