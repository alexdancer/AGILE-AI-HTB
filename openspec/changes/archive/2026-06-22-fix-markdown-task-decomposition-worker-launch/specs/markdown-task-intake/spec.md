## MODIFIED Requirements

### Requirement: Board accepts markdown task intake
The board SHALL allow an operator to submit a task description as multi-line markdown text or as an uploaded `.md` file for estimation. When markdown intake contains two or more deterministic task items, the system SHALL create one estimated task card per item instead of one card for the entire markdown document.

#### Scenario: Paste markdown into board estimator
- **WHEN** the operator pastes a multi-line markdown task description into the board estimator
- **AND** submits the estimate form
- **THEN** the estimator receives normalized markdown-derived task content
- **AND** the resulting task or tasks preserve enough source context to show they came from markdown intake

#### Scenario: Upload markdown file into board estimator
- **WHEN** the operator uploads a `.md` file to the board estimator
- **AND** submits the estimate form
- **THEN** the estimator receives decoded file-derived task content for each created card
- **AND** the route redirects back to the board after creating estimated task output

#### Scenario: Markdown checklist creates multiple task cards
- **WHEN** the operator submits markdown containing multiple checklist task items
- **THEN** the board creates one persisted task card for each checklist item
- **AND** each task card description is scoped to that item instead of the entire markdown document
- **AND** each task card records markdown source metadata including source type, item index, item count, and parent source identity

#### Scenario: Markdown without deterministic items remains one card
- **WHEN** the operator submits markdown that does not contain multiple deterministic task items
- **THEN** the board creates a single estimated task card using the normalized markdown content
- **AND** the task card records markdown source metadata
