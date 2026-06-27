## ADDED Requirements

### Requirement: Session report displays checkpoint results

The session report page SHALL display checkpoint results when a session has them. Each checkpoint SHALL show its name, a pass/fail indicator, and a compact details summary. When a session has no checkpoint results, the section SHALL be omitted.

#### Scenario: Session with passing checkpoints

- **WHEN** a session has checkpoint results `[{name: "budget_health", passed: true, details: {spent: 1600}}]`
- **AND** the operator views the session report
- **THEN** a "Checkpoints" section SHALL be visible
- **AND** "budget_health" SHALL be displayed with a green "PASS" pill
- **AND** the details SHALL be displayed as "spent=1600"

#### Scenario: Session with failing checkpoints

- **WHEN** a session has checkpoint results `[{name: "stuck_loop_score", passed: false, details: {score: 0.85}}]`
- **AND** the operator views the session report
- **THEN** "stuck_loop_score" SHALL be displayed with a red "FAIL" pill

#### Scenario: Session with no checkpoint results

- **WHEN** a session has zero checkpoint results
- **AND** the operator views the session report
- **THEN** no "Checkpoints" section SHALL be rendered
