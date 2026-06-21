## Why

Tasks now move from Running to Review after a successful Worker Run, but Review is a dead-end in the board UI. Operators need a clear review panel that can request an agent review, capture user-specific review prompts, approve work as Done, or Block reviewed work with a reason.

## What Changes

- Add Review task disposition actions on Review cards:
  - Agent Review: runs a control-plane/orchestrator model review against task, session, Worker Run, token, and evidence context, then stores/displays the response on the task card.
  - Mark Done: immediately moves a reviewed completed task to Done and records operator approval metadata.
  - Save/request with prompt: lets the operator type specific review focus or feedback; the prompt is saved and included in Agent Review when requested.
  - Block: moves the reviewed task to Blocked with an operator-provided reason.
- Keep Agent Review informational: it does not automatically move lifecycle state.
- Preserve prior Worker Run/session evidence and review prompts/results for audit when the task moves to Done or Blocked.
- Keep the model-layer split explicit: Agent Review uses the AGILE-AI-HTB control-plane/orchestrator model, not the Worker Adapter model/auth that performed the task.

## Capabilities

### New Capabilities
- `task-review-disposition`: Defines Review-stage operator actions, persisted review prompts/results, Agent Review behavior, Done approval, and Block disposition.

### Modified Capabilities
- `board-launch-selection`: Review cards must expose review actions and display the latest user review prompt and agent review response, extending the existing board Review display requirement.

## Impact

- Affected UI/templates: Review task cards on the board; display of review prompt, agent review summary, Done/Block actions.
- Affected API routes: new HTML form endpoints or equivalent task-action endpoints for Agent Review, Mark Done, Save Prompt, and Block.
- Affected model usage: control-plane/orchestrator model invocation for Agent Review, separate from Worker Adapter/coding harness models.
- Affected persistence: task metadata for review prompt, agent review result/status, review decision, reviewed timestamp, and blocked reason.
- Affected tests: board rendering for Review actions, route behavior for Done/Block/prompt/agent-review, and protection against invalid lifecycle transitions.
