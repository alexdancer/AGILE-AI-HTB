## MODIFIED Requirements

### Requirement: Model selector filters by selected adapter
The board launch form SHALL include a model selector populated from the selected adapter's allowed Worker models. Changing the adapter selection SHALL update the model dropdown to show only that adapter's allowed models.

#### Scenario: Adapter has allowed models
- **WHEN** operator selects an adapter with allowed models `["opencode/gpt-5.1", "gpt-5.1-codex"]`
- **THEN** the model dropdown shows those two models

#### Scenario: Adapter has discovered models but no allowed models
- **WHEN** operator selects an adapter with discovered models but an empty allowed model set
- **THEN** the model dropdown does not offer an unapproved fallback model
- **AND** launch guardrails keep the task from launching until at least one model is allowed

#### Scenario: Switching adapter updates model list
- **WHEN** operator changes adapter selection from OpenCode to Claude Code
- **THEN** the model dropdown updates to show Claude Code's allowed models
