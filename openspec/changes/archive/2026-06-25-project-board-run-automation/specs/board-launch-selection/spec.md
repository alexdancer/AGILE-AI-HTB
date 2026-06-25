## ADDED Requirements

### Requirement: Board live-refreshes active Worker Runs
The board SHALL keep active Worker Run status current without requiring the operator to click Refresh status manually.

#### Scenario: Running task completes while board is open
- **WHEN** an operator has the board open with a Running task
- **AND** the task's Worker Run completes successfully
- **THEN** the board SHALL update so the task appears in Review without requiring a manual Refresh status click

#### Scenario: Running task fails retryably while board is open
- **WHEN** an operator has the board open with a Running task
- **AND** the task's Worker Run fails retryably
- **THEN** the board SHALL update so the task appears in Estimated with inline launch failure evidence

#### Scenario: Manual refresh remains available
- **WHEN** live refresh is unavailable or disabled
- **THEN** the existing manual Refresh status action SHALL remain available for Running tasks

### Requirement: Board automation controls preserve manual launch
The board SHALL add automation controls without removing existing per-task Launch controls for Estimated tasks.

#### Scenario: Operator can still launch a single card manually
- **WHEN** an Estimated task appears on the board
- **THEN** the task card SHALL still expose the existing adapter/model launch form
- **AND** automation controls SHALL NOT be required to launch the task
