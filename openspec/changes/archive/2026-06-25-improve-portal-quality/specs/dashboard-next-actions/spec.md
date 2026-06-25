## ADDED Requirements

### Requirement: Next-action surfaces use consistent action styling
Dashboard and project next-action surfaces SHALL use consistent action-card or action-row styling and copy patterns.

#### Scenario: Dashboard next actions match Portal action pattern
- **WHEN** the dashboard renders Operator next actions
- **THEN** each action SHALL use the same shared visual pattern as project overview action cards or rows
- **AND** each action SHALL link to the existing page that handles the workflow

#### Scenario: Next-action copy is concise and operator-facing
- **WHEN** a next-action surface describes setup, launch, review, alarm, or board work
- **THEN** the copy SHALL name the operator action and the affected workflow without exposing internal implementation terms as the primary label
