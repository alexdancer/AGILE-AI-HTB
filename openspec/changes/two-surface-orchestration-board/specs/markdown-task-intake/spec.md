## ADDED Requirements

### Requirement: Pipeline Planning Inbox lists pending Proposed Task Breakdowns
The system SHALL list pending Proposed Task Breakdowns for the selected project in a Planning Inbox on the Pipeline Surface, so a breakdown remains reachable after task intake navigates the operator to the Task Breakdown Review page. Listing a pending breakdown SHALL NOT create a Task and SHALL NOT edit breakdown candidates inline; entries SHALL link to the authoritative Task Breakdown Review page.

#### Scenario: Pending breakdown appears in the Planning Inbox
- **WHEN** an operator submits Markdown intake that produces a Proposed Task Breakdown and then returns to the Pipeline Surface
- **THEN** the Planning Inbox SHALL list that pending breakdown with its source, candidate count, created time, and status
- **AND** the entry SHALL link to the authoritative Task Breakdown Review page

#### Scenario: Listing a breakdown does not create a task or allow inline edits
- **WHEN** the Planning Inbox lists a pending Proposed Task Breakdown
- **THEN** the breakdown SHALL remain a proposal awaiting review and SHALL NOT appear as an Estimated Task
- **AND** the Pipeline Surface SHALL NOT provide inline candidate editing

#### Scenario: Breakdowns are queryable per project
- **WHEN** the system builds the Planning Inbox for a project
- **THEN** it SHALL retrieve pending Proposed Task Breakdowns for that project via a project-scoped query
- **AND** breakdowns bound to other projects SHALL NOT appear
