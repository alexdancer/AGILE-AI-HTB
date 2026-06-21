## Context

The asynchronous Worker Run lifecycle now moves successful work from `Running` to `Review`, preserving stdout/stderr, token/session evidence, and optional git evidence. The board currently displays Review evidence and a session report link, but provides no operator action to disposition the task. This leaves completed tasks stuck in Review even when the operator wants to approve, block, or request an AI-assisted review.

The product has two distinct model layers that matter here:

```text
AGILE-AI-HTB control-plane/orchestrator model
  estimates tasks, summarizes/reviews evidence, writes reports

Worker Adapter / coding harness model
  OpenCode / Claude Code / Codex / Hermes runs the implementation task
```

Review actions belong to the control-plane/orchestrator layer. They should inspect the Worker Run evidence after the Worker Adapter has finished, not reuse or mutate the Worker Adapter launch contract.

## Goals / Non-Goals

**Goals:**

- Add a Review-card action panel for completed tasks in Review.
- Let operators request Agent Review and display the latest review response on the task card.
- Let operators type a specific review prompt/focus and persist it on the task.
- Let operators mark a Review task Done without requiring Agent Review.
- Let operators Block a Review task with a reason.
- Preserve task/session/Worker Run evidence when disposition actions change task status.
- Use the control-plane/orchestrator model for Agent Review, separate from Worker Adapter model/auth.

**Non-Goals:**

- No automatic merge, commit, deploy, PR, or code mutation from Agent Review.
- No automatic transition to Done or Blocked based only on Agent Review output.
- No streaming review transcript UI in this slice.
- No change to Worker Adapter tracking modes or launchability rules.
- No requirement that Agent Review can run when the control-plane model is unavailable; the UI should surface a clear failure instead.

## Decisions

### Decision: Review actions are explicit task action endpoints

Add focused Review action endpoints rather than overloading the generic task update route for browser forms. The board can submit normal HTML forms for:

- Agent Review
- Save review prompt / review focus
- Mark Done
- Block

Rationale: existing board actions already use form POSTs for launch and refresh. Dedicated endpoints keep lifecycle validation close to each action and avoid forcing browser forms through JSON-only `PUT /tasks/{task_id}`.

Alternative considered: use only `PUT /tasks/{task_id}`. Rejected for board UX because standard HTML forms cannot submit PUT without JavaScript and because Agent Review needs model invocation and evidence assembly, not just a field update.

### Decision: Agent Review stays informational

Agent Review stores a response on the task and leaves the task in Review. The operator still chooses Mark Done or Block.

Rationale: Review is the human/operator gate. Agent Review is advisory evidence, not an autonomous approval authority.

Alternative considered: auto-mark Done when Agent Review recommends approve. Rejected because it removes the explicit operator decision and makes failures harder to explain in the demo.

### Decision: Agent Review uses control-plane evidence assembly

The Agent Review prompt should include sanitized task and run context:

- task ID and description
- selected Worker Adapter, model, tracking mode, and launch mode
- Worker Run status, return code, stdout/stderr excerpts
- session/token evidence summary
- launch metadata such as diff summary or read-only report metadata when present
- latest operator review prompt/focus, if provided

The review model is the configured AGILE-AI-HTB control-plane/orchestrator model. This keeps Worker Adapter identity and tracking mode separate from review/summarization.

Alternative considered: spawn the same Worker Adapter again for review. Rejected because review is control-plane work and reusing the Worker Adapter would blur model/auth responsibilities.

### Decision: Persist review state in task metadata for this slice

Store the latest review prompt, latest Agent Review response, review status, and disposition metadata in task metadata. Existing Worker Run/session records remain the authoritative execution evidence.

Suggested metadata fields:

```json
{
  "review_prompt": "operator focus text",
  "agent_review": {
    "status": "completed | failed",
    "summary": "...",
    "recommendation": "approve | needs_changes | block | unknown",
    "findings": [],
    "reviewed_at": "...",
    "model": "..."
  },
  "review_decision": "accepted | blocked",
  "reviewed_at": "...",
  "blocked_reason": "..."
}
```

Rationale: this is a local/demo-first slice with one latest visible review on the card. A separate review history table can come later if multiple audit entries become necessary.

Alternative considered: create a `task_reviews` table now. Rejected as premature for the current demo UI; task metadata is consistent with existing launch evidence metadata.

### Decision: Mark Done and Block require completed Review context

Mark Done and Agent Review should only operate on tasks currently in Review with a completed backing session or completed Worker Run. Block can operate from Review and records the operator reason.

Rationale: this prevents accidental Done transitions for tasks that have not completed Worker execution while still allowing explicit blocking of reviewed work.

Alternative considered: allow Done from any status. Rejected because the board lifecycle already protects Running and pre-launch states.

## Risks / Trade-offs

- **Control-plane model unavailable** → Agent Review stores/displays a sanitized failure on the task and leaves the task in Review; Mark Done and Block remain available.
- **Large stdout/stderr or diff evidence** → Use existing sanitized/truncated evidence fields for the review prompt and card display; link to session report for detail.
- **Agent Review output is unstructured or low quality** → Store a concise fallback summary and raw sanitized response; do not let it change lifecycle state automatically.
- **Task metadata grows over time** → Store only latest prompt and latest Agent Review for this slice; defer review history until needed.
- **Operator blocks without useful reason** → Require non-empty block reason in the form/route and show validation failure on the board.
