## ADDED Requirements

### Requirement: Board task cards default to compact readable content

The board SHALL render task cards with a compact default view that keeps the task summary, key estimate/model metadata, and the current primary action visible while placing verbose evidence and diagnostics behind native expandable details.

#### Scenario: Long task description is compact by default

- **WHEN** a task has a long description
- **AND** the operator opens the board
- **THEN** the task card shows a shortened visual summary in the default card view
- **AND** the full task description remains available from the same card without navigating away

#### Scenario: Verbose run evidence is collapsed by default

- **WHEN** a task has Worker timeline events, launch stdout, stderr, Agent Review findings, or diagnostic evidence
- **AND** the operator opens the board
- **THEN** the verbose evidence is available behind native expandable details
- **AND** the card still shows the relevant primary action for its status without opening the details

#### Scenario: Existing board workflow remains unchanged

- **WHEN** the board renders Estimated, Running, Review, Done, and Blocked tasks
- **THEN** the existing board columns remain available
- **AND** the existing launch, refresh, review, done, and block actions remain available for their current statuses

### Requirement: Board displays actual launched model before recommendation

When a task has launch evidence for a Worker model, the board SHALL display that launched model as the primary model value. If the launched model differs from the recommended estimate model, the board SHALL preserve and display the recommended model as secondary evidence.

#### Scenario: Operator launches with recommended model

- **WHEN** a task is launched with the same model as `recommended_model`
- **THEN** the board shows that model as the primary model value
- **AND** the board does not duplicate the same model as a separate recommendation warning

#### Scenario: Operator overrides recommended model at launch

- **WHEN** a task has `recommended_model` set to `gpt-5.4-mini`
- **AND** the operator launches the task with `openai/gpt-5.5 --variant high`
- **THEN** the board shows `openai/gpt-5.5 --variant high` as the primary launched model value
- **AND** the board still shows `gpt-5.4-mini` as the recommended estimate model in secondary evidence

#### Scenario: Task has not launched yet

- **WHEN** a task has no launch model evidence
- **AND** it has a `recommended_model`
- **THEN** the board shows the recommended model as the primary model value
