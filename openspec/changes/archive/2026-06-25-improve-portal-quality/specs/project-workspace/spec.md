## ADDED Requirements

### Requirement: Project overview summarizes actionable repo state
The project overview SHALL summarize the selected repository's useful operator state before detailed repo profile data.

#### Scenario: Project overview shows next actions
- **WHEN** an authenticated operator opens `/projects/{project_id}`
- **THEN** the system SHALL show action cards or rows for the selected project's task board, Worker/setup readiness, running work, review-needed work, and relevant alarms or session evidence when available
- **AND** each action SHALL link to the existing workflow page that handles the action

#### Scenario: Project overview does not duplicate workflow forms
- **WHEN** the project overview shows setup, board, session, or alarm actions
- **THEN** it SHALL route the operator to existing workflow pages instead of duplicating launch, review, adapter verification, or alarm-resolution forms on the overview

### Requirement: Project overview keeps repo identity visible but secondary
The project overview SHALL keep repository identity and detected profile information available without making it the only useful content on the page.

#### Scenario: Repo profile remains visible after action summary
- **WHEN** an authenticated operator opens `/projects/{project_id}`
- **THEN** the page SHALL still show root path, branch, language/framework/package hints, test command, run command, and docs when available
- **AND** these details SHALL appear after or below the primary action/readiness summary
