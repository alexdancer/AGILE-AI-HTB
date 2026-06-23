## MODIFIED Requirements

### Requirement: Worker Run records review evidence
The system SHALL preserve sanitized Worker Run evidence for operator review after completion, including the configured Worker workdir and evidence of where files were changed when such evidence is available.

#### Scenario: Review evidence is captured
- **WHEN** a Worker Run completes successfully
- **THEN** the system stores sanitized stdout and stderr evidence
- **AND** records session/token evidence
- **AND** records configured workdir and command cwd evidence
- **AND** records git diff, porcelain, or filesystem evidence when the run is associated with a connected project root or configured workdir

#### Scenario: Workdir mismatch prevents completed-work review
- **WHEN** a Worker Run exits successfully
- **AND** the Worker command evidence indicates files were read or edited outside the configured workdir
- **AND** the configured workdir has no expected output or file-change evidence
- **THEN** the system marks the Worker Run failed with workdir mismatch evidence
- **AND** the task returns to Estimated for retry
- **AND** the task card or metadata shows the configured workdir and suspicious outside paths
