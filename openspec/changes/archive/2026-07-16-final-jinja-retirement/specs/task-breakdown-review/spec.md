## MODIFIED Requirements

### Requirement: Breakdown review page
The system SHALL provide a separate canonical review page for Proposed Task Breakdowns rather than representing breakdown review as an Orchestration Board column or Task state. When the complete React build is available, `/task-breakdowns/{breakdown_id}/review` SHALL render inside the React Portal shell; when the build is missing or partial, the same canonical URL SHALL return the missing-build recovery response.

#### Scenario: Markdown intake redirects to review page
- **WHEN** Markdown intake successfully produces a Proposed Task Breakdown
- **THEN** the operator is directed to `/task-breakdowns/{breakdown_id}/review` for that durable review record
- **AND** the Orchestration Board remains limited to Task lifecycle columns

#### Scenario: Built canonical review opens in React
- **WHEN** an authenticated operator opens an existing Task Breakdown Review while the complete frontend build is available
- **THEN** FastAPI SHALL return the React shell for the canonical review URL
- **AND** React SHALL render the review inside the shared Portal chrome
- **AND** no `/app/task-breakdowns` alias SHALL be introduced

#### Scenario: Missing or partial build returns the recovery response at the canonical review
- **WHEN** an authenticated operator opens an existing Task Breakdown Review while the frontend build is missing or partial
- **THEN** FastAPI SHALL return the missing-build recovery response at the same canonical URL
- **AND** the acceptance and recovery workflow SHALL be unavailable until the frontend is built, rather than diverting to a server-rendered review

#### Scenario: Unknown review stays backend-authoritative
- **WHEN** an authenticated operator opens the canonical review URL for an unknown breakdown id
- **THEN** FastAPI SHALL return `404`
- **AND** a complete React build SHALL NOT turn the unknown review into a successful shell-only page

#### Scenario: Accepting review creates estimated tasks
- **WHEN** the operator accepts one or more candidate tasks from the breakdown review page
- **THEN** the system immediately sends the accepted candidates to Task Estimation
- **AND** creates Estimated Orchestration Board Tasks for successful estimates
- **AND** returns the operator to the canonical project-scoped or global Orchestration Board
