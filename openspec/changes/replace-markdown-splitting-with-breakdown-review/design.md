## Context

The current Markdown intake path fixed a one-card collapse by extracting deterministic checklist/task bullets and creating one Estimated task card per extracted item. That solved oversized estimates but created a worse product failure: Markdown bullets are not always Tasks. Constraints, non-goals, and verification steps can be promoted into bad standalone board cards, for example “Do not add network dependencies.”

The domain model now treats Markdown structure as evidence for the Task Breakdown Agent, not as the source of truth for Tasks. The AGILE Board remains portal-first and should only contain estimated, launchable-or-guardrail-blocked Tasks, not pre-task planning artifacts.

## Goals / Non-Goals

**Goals:**

- Replace direct deterministic Markdown-to-Task creation with a durable Task Breakdown Review flow.
- Preserve the `/to-issues` philosophy: proposed work items are independently grabbable vertical slices, not raw bullets.
- Keep constraints, non-goals, and verification notes visible and preserved without estimating them as standalone work.
- Track Task Breakdown Agent spend as `task_breakdown` Orchestration Tokens.
- Let accepted candidates immediately enter Task Estimation and create Estimated board cards.
- Replace old tests that bless deterministic splitting with product-flow tests and golden decomposition fixtures.

**Non-Goals:**

- No full planning editor with arbitrary split/merge/drag-reorder behavior in the first slice.
- No hard inter-task dependency enforcement in the first slice.
- No deterministic splitting quick-import or fallback mode.
- No change to Worker Adapter identity or tracking modes.
- No hidden helper LLM calls outside the harness control-plane transport/token ledger path.

## Decisions

### 1. Persist Proposed Task Breakdowns before Task creation

Markdown uploads, Markdown paste, and clearly oversized plain text create a durable review record before any board Task rows are created. The record stores source metadata, agent output, candidates, rejected/non-task items, constraints, failure details when applicable, model identity, and linked orchestration token/session evidence.

Alternative considered: transient hidden-form review state. Rejected because the harness needs auditability, retry/resume, debugging, and evidence for orchestration token spend.

### 2. Use a separate review page, not a board column

The intake route redirects to a dedicated breakdown review page such as `/task-breakdowns/{id}/review`. Accepting candidates runs Task Estimation and returns to `/board` with Estimated cards.

Alternative considered: add a “Breakdown Review” board column. Rejected because Proposed Task Breakdowns are not Tasks and would pollute the AGILE Board lifecycle.

### 3. Markdown is always review-first

Markdown upload/paste always shows review, including single-task decisions. Short plain text can continue directly to Task Estimation; oversized plain text may enter breakdown review.

Alternative considered: auto-create high-confidence candidates. Rejected for the first slice because a bad split is highly visible and undermines trust.

### 4. Deterministic Markdown parsing becomes a hint only

Existing bullet/checklist extraction may be reused to provide structure hints to the Task Breakdown Agent prompt or fixture pre-processing, but it must not directly create Tasks or serve as a fallback when model output fails.

Alternative considered: keep deterministic quick import. Rejected because it reintroduces the exact failure mode.

### 5. Failure is explicit and recoverable

If the Task Breakdown Agent is unavailable, over budget, or returns invalid structure, the review page shows a breakdown-failed/manual recovery state. The operator can retry, create manual candidates, create one manual candidate from the source, or cancel. The system must not silently create a giant Estimated task or fall back to deterministic splitting.

### 6. Task Breakdown Model is configurable separately

Task Breakdown Agent uses a separate configurable Task Breakdown Model in the control-plane/orchestrator layer. It may default stronger than the estimator while still tracking spend as `task_breakdown` Orchestration Tokens. Worker Adapter models remain separate.

Alternative considered: reuse estimator model only. Rejected because decomposition quality is product-critical and should be tunable independently.

## Risks / Trade-offs

- Stronger breakdown model increases orchestration spend → Track it separately as `task_breakdown` and keep short plain text on the direct-estimation path.
- Persisting review records adds schema/UI work → Worth it for auditability and retry/resume evidence.
- Review-first adds one click before imported Markdown becomes cards → Worth it because the failure mode is bad visible Tasks.
- Agent output can still be wrong → Golden fixtures, explicit rejected items, and practical editing reduce the risk.
- Existing tests and docs encode deterministic splitting → This change must replace those assertions rather than layering a new flow beside stale behavior.
