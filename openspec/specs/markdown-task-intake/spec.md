# markdown-task-intake Specification

## Purpose
Define how operators can submit multi-line markdown task descriptions or markdown files for estimation from the board while preserving deterministic source handling and clear validation behavior.

## Requirements

### Requirement: Board accepts markdown task intake
The board SHALL allow an operator to submit a task description as multi-line markdown text or as an uploaded `.md` file for estimation.

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

### Requirement: Markdown file input has deterministic precedence
When both pasted markdown text and an uploaded `.md` file are submitted, the system SHALL use the uploaded file content as the estimator input and record the intake source as file-based markdown.

#### Scenario: File wins over pasted text
- **WHEN** the operator submits both textarea markdown and a `.md` upload
- **THEN** the estimator uses the uploaded file content
- **AND** the pasted text is not mixed into the estimator prompt

### Requirement: Markdown intake validates usable content
The markdown intake route SHALL reject empty markdown input and unsupported uploaded file types with a clear validation error.

#### Scenario: Empty markdown is rejected
- **WHEN** the operator submits an empty textarea and no file
- **THEN** the board shows a validation error and no task is created

#### Scenario: Unsupported file type is rejected
- **WHEN** the operator uploads a non-markdown file to the estimator
- **THEN** the board shows a validation error and no task is created
