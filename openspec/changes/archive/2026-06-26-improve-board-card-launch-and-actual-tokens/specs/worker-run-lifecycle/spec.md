## MODIFIED Requirements

### Requirement: Worker Run success moves task to Review
The system SHALL move the task from Running to Review when the Worker Run finishes successfully and required runtime evidence is present, and SHALL persist the task's actual Worker execution token total from authoritative usage evidence.

#### Scenario: Successful worker run enters Review
- **WHEN** a background Worker Run exits with return code 0
- **AND** required token usage evidence for the selected tracking mode is present
- **THEN** the system marks the Worker Run `completed`
- **AND** the associated task moves to Review
- **AND** the associated task records `actual_tokens` as the Worker execution token total for that completed run's session.
