## Why

The React AGILE Board currently sends Markdown and oversized-task intake out of the shell to the Jinja Task Breakdown Review, interrupting the primary intake → review → estimate workflow. The canonical review surface should migrate now that React Sessions/Report parity is complete, while preserving the existing backend-authoritative acceptance and failure-recovery behavior.

## What Changes

- Make canonical `/task-breakdowns/{breakdown_id}/review` build-aware: serve React when the complete frontend build exists and preserve the current Jinja page as missing/partial-build fallback.
- Add an authenticated, exact, bounded, redacted Task Breakdown Review JSON projection derived from the existing durable review record and backend normalization rules.
- Add a React review view inside the shared Portal chrome with full editable parity for candidate selection, kind, execution mode, title, objective, prompt, acceptance criteria, proof, constraints, HITL reason, slicing evidence, dependencies, likely entry points, global contract, global constraints, and verification.
- Keep rejected items, non-goals, recommended sequence, source/model/session/failure evidence, and Repo Context Brief evidence visible, using progressive disclosure for dense secondary detail.
- Keep pre-acceptance edits browser-local, warn before leaving with unsaved edits, and persist reviewed candidates only after `Accept selected and estimate`.
- Add explicit negotiated JSON outcomes to the existing Accept, Retry, and Manual Candidate actions while preserving their current HTML form redirects and backend authority.
- Preserve accepted-review idempotency, failed-review manual recovery, project-scoped board return, auth, unknown-review `404`, and no-Task-before-acceptance behavior.
- Add only the minimal monotonic Task Breakdown revision migration required for correct compare-and-set fencing; add no autosave/draft persistence, generalized form framework, Task Breakdown Agent change, estimation change, or Jinja retirement.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-breakdown-review`: Extend the canonical review contract to React presentation, full editable information parity, browser-local draft safety, and negotiated action outcomes without changing when Tasks are materialized.
- `react-portal-shell`: Extend build-aware canonical route ownership, authenticated bounded handoffs, client routing, fallback behavior, and shared-shell navigation to Task Breakdown Review.

## Impact

- FastAPI Task Breakdown Review route selection, shared context/projection helpers, and negotiated Accept/Retry/Manual outcomes under `src/agile_ai_htb/routes/tasks.py` and the React handoff layer.
- React route parsing, Task Breakdown Review view/controller, navigation guard, shared styling, and frontend tests under `frontend/`.
- Portal endpoint/auth/fallback/projection/action tests, primarily under `tests/api/test_task_estimation.py` and `tests/portal/test_react_shell.py`.
- Existing Jinja template remains the parity oracle and missing/partial-build fallback; Task Breakdown Agent output, Task Estimation, Worker routing, and created Task semantics remain unchanged. Persistence adds only a defaulted monotonic Task Breakdown revision used for concurrency fencing.
