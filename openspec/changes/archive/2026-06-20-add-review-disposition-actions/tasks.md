## 1. Review Action Backend

- [x] 1.1 Add focused Review action request handling for saving review prompt, requesting Agent Review, marking Done, and blocking tasks from Review.
- [x] 1.2 Enforce lifecycle validation so Mark Done and Agent Review require a Review task with completed Worker Run or completed session evidence, and invalid actions preserve task status with a clear error.
- [x] 1.3 Persist review metadata on the task, including latest review prompt, Agent Review status/result, recommendation when available, review decision, reviewed timestamp, and blocked reason.
- [x] 1.4 Preserve existing Worker Run, session, token, launch stdout/stderr, and diff evidence when Review actions move tasks to Done or Blocked.

## 2. Agent Review

- [x] 2.1 Build sanitized Agent Review context from task description, Worker Run evidence, session/token evidence, launch metadata, stdout/stderr excerpts, and latest operator review prompt.
- [x] 2.2 Invoke Agent Review through the configured control-plane/orchestrator model connection, not through Worker Adapter model/auth.
- [x] 2.3 Store a successful Agent Review response on the task and keep the task in Review.
- [x] 2.4 Store and display a sanitized Agent Review failure when the control-plane model is unavailable or the review call fails, while leaving Mark Done and Block available.

## 3. Board UI

- [x] 3.1 Update Review task cards to show a review action panel with Agent Review, Mark Done, Block, and an optional review prompt/focus input.
- [x] 3.2 Display the latest saved operator review prompt on the Review task card.
- [x] 3.3 Display the latest Agent Review summary/response and recommendation on the Review task card.
- [x] 3.4 Display Review action validation errors on the board without losing task evidence.

## 4. Tests and Verification

- [x] 4.1 Add route tests proving Mark Done moves a valid Review task with completed evidence to Done and rejects non-Review tasks.
- [x] 4.2 Add route tests proving Save Prompt keeps the task in Review and persists/displays the prompt.
- [x] 4.3 Add route tests proving Agent Review uses the control-plane model, stores the response, displays it on the card, and does not change lifecycle status.
- [x] 4.4 Add route tests proving Agent Review failure is displayed while the task remains in Review.
- [x] 4.5 Add route tests proving Block requires a reason and moves a valid Review task to Blocked with preserved evidence.
- [x] 4.6 Run targeted Review/board tests and the full `uv run pytest` suite before marking tasks complete.
