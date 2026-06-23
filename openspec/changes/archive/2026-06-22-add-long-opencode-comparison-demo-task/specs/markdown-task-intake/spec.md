## MODIFIED Requirements

### Requirement: Board accepts markdown task intake
The board SHALL allow an operator to submit a task description as multi-line markdown text or as an uploaded `.md` file for estimation, including long demo task markdown artifacts used for OpenCode comparison runs.

#### Scenario: Paste markdown into board estimator
- **WHEN** the operator pastes a multi-line markdown task description into the board estimator
- **AND** submits the estimate form
- **THEN** the estimator receives the normalized markdown content
- **AND** the resulting task or tasks preserve enough source context to show they came from markdown intake

#### Scenario: Upload markdown file into board estimator
- **WHEN** the operator uploads a `.md` file to the board estimator
- **AND** submits the estimate form
- **THEN** the estimator receives the decoded file content as the task description
- **AND** the route redirects back to the board after creating estimated task output

#### Scenario: Submit long OpenCode comparison task markdown
- **WHEN** the operator submits the long synthetic OpenCode comparison task markdown through markdown intake
- **THEN** the estimator receives the task content as a normal markdown task input
- **AND** the intake source remains identifiable as markdown-based demo task input without changing existing file precedence or validation behavior
