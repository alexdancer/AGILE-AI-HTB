## ADDED Requirements

### Requirement: Auto Agent Review does not decide disposition
Automatic Agent Review SHALL be advisory evidence only and SHALL NOT replace operator Review Disposition.

#### Scenario: Auto review approval remains in Review
- **WHEN** Auto Agent Review completes with an approval or positive recommendation
- **THEN** the task SHALL remain in Review
- **AND** the operator SHALL still choose Mark Done before the task moves to Done

#### Scenario: Auto review findings remain in Review
- **WHEN** Auto Agent Review reports findings or a negative recommendation
- **THEN** the task SHALL remain in Review
- **AND** the operator SHALL still choose Block with a reason before the task moves to Blocked

#### Scenario: Auto review failure does not change task state
- **WHEN** Auto Agent Review fails due to control-plane model or parsing errors
- **THEN** the task SHALL remain in Review
- **AND** the Review card SHALL show review failure evidence without moving the task to Done or Blocked
