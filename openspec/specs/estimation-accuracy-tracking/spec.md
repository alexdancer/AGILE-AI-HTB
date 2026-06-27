# estimation-accuracy-tracking Specification

## Purpose

Define how completed task estimates are compared against actual token usage and surfaced on the dashboard for calibration.

## Requirements

### Requirement: Accuracy stats computed from completed tasks

The system SHALL compute aggregate estimation accuracy metrics from all tasks where `status = 'Done'`, `estimate_tokens IS NOT NULL`, and `actual_tokens IS NOT NULL AND actual_tokens > 0`.

Metrics SHALL include:
- `completed_count`: number of completed tasks with both estimate and actual tokens
- `median_error_ratio`: median of `actual_tokens / estimate_tokens` across completed tasks
- `within_2x_pct`: percentage of completed tasks where `0.5 <= actual_tokens / estimate_tokens <= 2.0`

Error ratio = actual_tokens / estimate_tokens. A ratio of 1.0 means perfect accuracy. A ratio > 1.0 means the task was underestimated. A ratio < 1.0 means the task was overestimated.

#### Scenario: Compute accuracy with completed tasks

- **WHEN** there are 5 completed tasks with estimates of [500, 300, 1000, 200, 800] and actuals of [550, 280, 1400, 180, 750]
- **THEN** `completed_count` SHALL be 5
- **AND** the error ratios are [1.10, 0.933, 1.40, 0.90, 0.9375]
- **AND** `median_error_ratio` SHALL be approximately 0.9375
- **AND** `within_2x_pct` SHALL be 100.0 (all five are within 0.5x–2.0x)

#### Scenario: No completed tasks

- **WHEN** there are zero tasks with `status = 'Done'` and both estimate and actual tokens
- **THEN** `completed_count` SHALL be 0
- **AND** `median_error_ratio` SHALL be null
- **AND** `within_2x_pct` SHALL be null

#### Scenario: Tasks with missing actuals are excluded

- **WHEN** a task has `status = 'Done'` and `estimate_tokens = 500` but `actual_tokens IS NULL`
- **THEN** that task SHALL be excluded from accuracy computation
- **AND** `completed_count` SHALL NOT include it

### Requirement: Accuracy stats displayed on dashboard

The dashboard (`/dashboard`) SHALL display the accuracy summary when `completed_count >= 3`. When `completed_count < 3`, the dashboard SHALL display "Not enough completed tasks for accuracy tracking" instead of raw numbers.

#### Scenario: Dashboard shows accuracy with sufficient data

- **WHEN** `completed_count >= 3`
- **THEN** the dashboard SHALL display the completed count, median error ratio (formatted to 2 decimal places), and within-2x percentage
- **AND** the median error ratio SHALL be labeled with a directional indicator: "optimistic" when > 1.05, "conservative" when < 0.95, "accurate" otherwise

#### Scenario: Dashboard shows placeholder with insufficient data

- **WHEN** `completed_count < 3`
- **THEN** the dashboard SHALL display "Not enough completed tasks for accuracy tracking"
- **AND** raw numbers SHALL NOT be displayed

### Requirement: Estimate form shows project context indicator

When estimating from a project board, the estimate form SHALL display an indicator showing the project name and that project context is being used. When estimating without a connected project, the form SHALL display "No project context — estimate will be less accurate."

#### Scenario: Project board estimate form

- **WHEN** the operator views the estimate form on a project board
- **THEN** the form SHALL display "Estimating with project context: <project name>"

#### Scenario: Global board estimate form

- **WHEN** the operator views the estimate form on the global board without a connected project
- **THEN** the form SHALL display "No project context — estimate will be less accurate"
