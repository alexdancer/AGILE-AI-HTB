## Context

Connected-project intake currently reaches Task Breakdown with the submitted source text, Markdown structure hints, and light project metadata. Estimation and Worker launch already call `build_repo_context_brief()` and use bounded repo docs, manifests, entrypoints, test commands, and a file sample.

The gap is narrow: card slicing happens before estimation, so the Task Breakdown Agent can propose generic implementation cards even when a connected project has enough bounded repo context to name likely verification commands, entrypoints, or repo constraints.

## Goals / Non-Goals

**Goals:**

- Reuse the existing Repo Context Brief for connected-project Task Breakdown requests.
- Keep no-project/global intake behavior unchanged.
- Preserve the Proposed Task Breakdown review as the human gate before AGILE Board Tasks are created.
- Persist enough metadata for operators to audit that repo context was used.

**Non-Goals:**

- No full repository prompt dump.
- No embeddings, RAG, AST/codegraph service, or background indexer.
- No automatic task acceptance, dependency enforcement, or Worker launch change.
- No new Worker Adapter behavior.

## Decisions

1. **Reuse `build_repo_context_brief()` instead of adding a new analyzer.**
   - Rationale: it already provides bounded docs/manifests/entrypoints/test commands and secret redaction.
   - Alternative rejected: whole-repo analysis or semantic indexing; too large for this slice and not needed to improve card wording.

2. **Pass repo context as structured Task Breakdown input, not by appending it to source text.**
   - Rationale: keeps the original source contract separate from planning context and avoids polluting accepted Acceptance Verification prompts.
   - Alternative rejected: prepend `repo_context_prompt()` to the source text; simpler but blurs user task text with repo hints.

3. **Build context only when intake metadata has a valid connected project root.**
   - Rationale: global task intake should stay unchanged, and invalid/missing project roots should not block manual breakdown recovery.
   - Alternative rejected: require repo context for all breakdowns; global board use still exists.

4. **Store a bounded context summary/source list on the breakdown record.**
   - Rationale: review/session evidence should explain why the Control Plane proposed repo-aware slices without exposing secrets or unbounded text.
   - Alternative rejected: store only a boolean; not auditable enough.

## Risks / Trade-offs

- Repo context may still be shallow → keep labels as a bounded brief and keep Workers responsible for deep file inspection before editing.
- Brief generation can fail on unreadable paths → fall back to no-context breakdown and record no repo-context metadata rather than blocking intake.
- Prompt size grows → reuse existing brief caps and avoid adding more source reads in this slice.
- Operators may overtrust repo-aware cards → review page remains human-gated before task creation.
