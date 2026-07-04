## Context

The current Task Breakdown Agent already separates Markdown/oversized intake from Task Estimation and creates Proposed Task Breakdown records before AGILE Board Tasks. It preserves global contract context, distinguishes `implementation` from `acceptance_verification`, and uses bounded Repo Context Brief input for connected projects.

The missing layer is a stronger, explicit task-slicing doctrine. The existing prompt says “vertical-slice task candidates,” but it does not force the Control Plane to reject unnecessary/speculative cards, classify AFK versus HITL slices, prove why each card is not over- or under-split, or require a smallest executable proof per candidate.

## Goals / Non-Goals

**Goals:**

- Encode the senior-agent task-slicing logic as Harness-owned Control Plane policy, not as literal Worker skill loading.
- Make AGILE Board candidates independently launchable, reviewable, and verifiable before they reach Task Estimation.
- Preserve current product guarantees: human review before board creation, compact implementation prompts, Acceptance Verification for integrated artifacts, and Worker-side deep repo inspection.
- Keep the first implementation boring: prompt/schema/metadata/tests, with minimal review UI changes needed to expose/edit key fields.

**Non-Goals:**

- No literal Hermes skill invocation, skill-file loading, or Worker-runtime skill selection from the Harness.
- No RAG, embeddings, semantic index, AST index, or whole-repo prompt dump.
- No new Worker Adapter behavior, tracking mode, budget semantics, or provider client changes.
- No automatic repair-task creation from failed Acceptance Verification or failed Worker runs.
- No hard dependency enforcement between accepted board Tasks in this slice.
- No conversion of every short plain-text intake into Task Breakdown review unless separately approved.

## Decisions

### 1. Add a Task Slicing Policy module

Create a small module such as `src/agile_ai_htb/task_slicing_policy.py` that owns the policy text and allowed values used by Task Breakdown. `task_breakdown.py` should compose the Task Breakdown Agent system prompt from the agent identity, the reusable policy, and the output schema.

Alternative considered: keep expanding the inline `_system_prompt()` string. Rejected because the policy is now product logic that needs focused tests and readable maintenance.

### 2. Keep candidate kind narrow, add execution mode separately

Keep `kind` as `implementation` or `acceptance_verification` for compatibility with existing review/launch behavior. Add an orthogonal `execution_mode` field with `AFK` or `HITL` to indicate whether a Worker can complete the task without waiting for operator input.

Alternative considered: add new candidate kinds such as `diagnosis`. Rejected for this slice because candidate kind currently controls Acceptance Verification behavior. Diagnostic work can be represented as an implementation candidate whose objective/proof says “build the repro/feedback loop.”

### 3. Require candidate quality evidence

Each candidate should carry enough structured evidence for the operator to audit why it deserves a board card:

- objective
- proof or verification path
- why this task exists
- why it is not smaller
- why it is not larger
- dependencies by candidate title when unavoidable
- likely repo entry points from Repo Context Brief when known
- execution mode and HITL reason when applicable

This evidence should be persisted on the Proposed Task Breakdown and accepted Task metadata. The Worker-facing Task description should include only the fields needed for execution: objective, prompt, compact global contract, constraints, acceptance criteria, dependencies, and proof.

Alternative considered: store the evidence only in the LLM rationale. Rejected because operators need auditable per-card reasons, not one generic response rationale.

### 4. Strengthen rejection rules

The Task Breakdown Agent should explicitly reject or classify as non-task source items that are constraints, non-goals, verification notes, setup prose, duplicate bullets, speculative abstractions, horizontal layer work, or context-only text. Rejected items remain visible on the review page.

Alternative considered: allow the review page to clean up weak candidates manually. Rejected because the Harness promise is governed task creation; obvious non-tasks should not reach estimation by default.

### 5. Keep repo awareness bounded

Continue using Repo Context Brief as Task Breakdown input for connected-project intake. The policy may use it to name likely files, tests, docs, or entry points, but must not claim deep source analysis or replace Worker execution-time inspection.

Alternative considered: add deep code indexing before breakdown. Rejected as too expensive and unnecessary for the first policy-strengthening slice.

## Risks / Trade-offs

- More schema fields can make LLM output validation more fragile. → Mitigate with deterministic fake-LLM tests, strict validators, and clear recovery to manual breakdown when validation fails.
- More candidate metadata can clutter the review UI. → Mitigate by showing summary fields by default and putting detailed evidence in native `<details>` blocks or metadata until a richer editor is needed.
- Stronger policy can under-split work by preferring fewer tasks. → Mitigate with explicit “why not larger” evidence and Acceptance Verification preservation.
- Stronger policy can over-constrain creative plans. → Mitigate by keeping operator edit/reject controls and avoiding hard dependency blocking.
- Repo entry-point hints can be wrong because Repo Context Brief is shallow. → Mitigate by labeling them as likely entry points and leaving deep inspection to the Worker Adapter.
