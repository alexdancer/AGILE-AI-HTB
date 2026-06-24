## Context

The current breakdown review flow already treats Markdown structure as evidence instead of directly creating Tasks from bullets. That fixes raw deterministic splitting, but it does not fully protect the original source contract once work is split into multiple smaller slices.

Demo evidence showed the failure mode: individually plausible slices can produce thinner implementation results and miss integrated contract details such as report shape, ID conventions, schema fields, or synthetic-data invariants. The fix must preserve the project thesis: do not run the whole thing as one Task; create better slices and add explicit final acceptance proof for integrated artifacts.

## Goals / Non-Goals

**Goals:**

- Preserve one editable global contract summary on each Proposed Task Breakdown.
- Add explicit candidate kind so the Harness does not infer verification intent from prose.
- Auto-propose an Acceptance Verification candidate for multi-slice integrated artifacts.
- Keep Acceptance Verification as a normal estimated AGILE Board Task with its own budget, Worker Run, and Review Disposition.
- Keep the first implementation simple: prompt/schema/tests plus minimal review-page display/edit support.

**Non-Goals:**

- No board group headers or global accepted-state UI in this change.
- No hard launch-order dependency enforcement.
- No automatic repair Task creation from failed Acceptance Verification findings.
- No full planning editor, arbitrary task taxonomy, drag-reorder, or split/merge UI.
- No requirement for a second Worker Adapter/model before Acceptance Verification can launch.

## Decisions

### 1. Candidate kind is explicit and small

Candidate Tasks get a constrained kind field:

- `implementation`
- `acceptance_verification`

Rejected/non-task items remain outside candidate Tasks. The review page may let the operator edit candidate kind, but only between those two values.

Alternative considered: infer verification tasks from title or prompt text. Rejected because the board, estimator, tests, and future review logic need stable intent without brittle prose matching.

### 2. The breakdown has one global contract summary

The Task Breakdown Agent writes one `global_contract_summary` for the Proposed Task Breakdown. The review page displays and allows editing it. Accepted implementation candidates inherit the summary and relevant constraints before Task Estimation.

Acceptance Verification receives both the summary and the full original source contract. This keeps implementation slices aligned without copying the full source into every slice.

Alternative considered: each slice writes its own global-context summary. Rejected because per-slice summaries can drift and lose the same contract details the feature is meant to preserve.

### 3. Acceptance Verification is auto-proposed for integrated artifacts

When the agent splits work that produces one integrated artifact such as a CLI, app, API, demo, or report, it auto-proposes an `acceptance_verification` candidate recommended last. The operator can reject it if the accepted slices are genuinely independent.

Acceptance Verification is not a whole-task rerun. It should validate the combined artifact against the original contract using the smallest executable proof available, such as tests, CLI smoke checks, API calls, artifact parsing, or invariant scans, and then produce human-readable findings.

Alternative considered: make Acceptance Verification mandatory and non-rejectable. Rejected because some breakdowns contain genuinely independent work where final integrated proof is unnecessary.

### 4. Preserve sequence without hard dependencies

Acceptance Verification is recommended last and preserved in sequence metadata or creation order. This change does not add launch-order blocking or board grouping.

Alternative considered: block launch of Acceptance Verification until all implementation slices are Done. Rejected for the first slice because it adds board state complexity and is not needed to validate the prompt/schema quality fix.

### 5. Failed Acceptance Verification blocks; it does not auto-create repairs

A failed Acceptance Verification Task should move to Blocked with findings. The operator decides whether findings are defects, scope creep, or acceptable limitations and may manually create or approve follow-up Tasks.

Alternative considered: automatically create repair Tasks from findings. Rejected because that can recreate bad slicing from unreviewed failure prose.

## Risks / Trade-offs

- Schema change touches persistence, prompt parsing, tests, and UI → Keep fields minimal and backwards-compatible where existing records lack them.
- Acceptance Verification could become disguised whole-task implementation → Prompt and tests must frame it as verification/proof only.
- More text in each implementation Task can increase estimates → Inherit a brief summary, not the full source contract.
- Agent may over-propose Acceptance Verification → Operator can reject the candidate during review.
- No hard ordering means users can launch it early → Accept for first slice; sequence metadata and clear title/kind make intended order visible.
