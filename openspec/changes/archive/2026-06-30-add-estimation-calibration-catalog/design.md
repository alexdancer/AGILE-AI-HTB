## Context

Task Estimation already produces structured Worker-token estimates and stores Worker actuals separately from Control Plane spend. The dashboard can compute completed-task accuracy, but the product does not yet have enough live completed runs to make historical calibration reliable. Operators need a fixture-led way to seed calibration data manually, keep it reviewable, and later supplement it with SQL-derived live history.

The first slice must improve Worker execution token estimates only. It must not change budget semantics, task `actual_tokens`, Worker launch rules, or Review/acceptance scoring.

## Goals / Non-Goals

**Goals:**

- Define and load a manual estimation calibration catalog for Worker execution token estimates.
- Support both checked-in sample/default catalogs and repo-local `.htb/estimation_calibration.yaml` operator catalogs.
- Validate checked-in/test data strictly and local operator data leniently with warnings.
- Select a bounded set of relevant cases using deterministic filters and lexical ranking.
- Inject a read-only calibration summary into estimator context when relevant cases exist.
- Preserve a SQL/live-history seam for future completed-task calibration.
- Add regression coverage proving catalog schema, relevance selection, estimator prompt inclusion, and estimate-band eval behavior.

**Non-Goals:**

- No embeddings, vector database, RAG, or semantic indexer.
- No Portal editor UI for calibration cases.
- No automatic numeric multipliers, clamps, or post-processing of estimator output.
- No budget semantic changes; launch budget checks remain based on Worker execution token estimates and Worker execution spend.
- No acceptance-quality, pass/fail, or delivery-risk scoring in this slice.

## Decisions

1. **Use fixture-led manual calibration first.**
   - Decision: introduce an operator-authored catalog before relying on live SQL history.
   - Rationale: current completed-run history is too thin to calibrate automatically, while manual cases can be reviewed and tested.
   - Alternative rejected: SQL-only historical calibration first, because sparse history would produce unstable or empty guidance.

2. **Use practical structured cases.**
   - Decision: each case includes `id`, `task_description`, `project_profile`, `task_kind`, `complexity`, `recommended_model`, `expected_tokens_min`, `expected_tokens_max`, optional `actual_tokens`, and `rationale`.
   - Rationale: these fields are enough to test estimate bands and build readable prompt context without requiring full Worker logs.
   - Alternative rejected: full evidence records, because they would make manual authoring too heavy for the first slice.

3. **Keep local operator catalog separate from checked-in examples.**
   - Decision: provide a checked-in sample/default catalog for schema examples and tests, plus `.htb/estimation_calibration.yaml` for operator-specific cases.
   - Rationale: checked-in cases document the contract; local cases can include project-specific operational history without being committed.
   - Alternative rejected: only checked-in data, because operators need local calibration without publishing history.

4. **Summarize catalog cases as read-only estimator context.**
   - Decision: selected cases are rendered into a bounded calibration summary included in the estimator prompt/payload.
   - Rationale: the estimator remains responsible for the final structured estimate, and the rationale remains auditable.
   - Alternative rejected: numeric multipliers or clamps, because they hide calibration effects and can silently distort budget gates.

5. **Use deterministic relevance selection.**
   - Decision: filter by available structured fields such as project profile, task kind, complexity, and recommended model, then rank by lexical token overlap against the task description, capped to top N / max chars.
   - Rationale: this is cheap, explainable, and testable.
   - Alternative rejected: embeddings/RAG, because it adds infrastructure before proving that catalog calibration helps.

6. **Preserve a SQL calibration seam without using it as the first source of truth.**
   - Decision: design selection/summary code around a common calibration-case shape so future completed Done tasks can be converted into calibration candidates.
   - Rationale: future live history should supplement manual cases once enough data exists.

## Risks / Trade-offs

- Manual cases may encode bad estimates → Mitigation: strict validation for checked-in/test catalogs, visible rationale fields, estimate-band evals, and local warnings for malformed cases.
- Catalog context can bias the estimator incorrectly → Mitigation: render selected cases as examples/ranges only, not as authoritative multipliers or clamps.
- Local `.htb` data may be incomplete or malformed → Mitigation: ignore invalid local cases with warnings instead of blocking estimation.
- Lexical ranking may miss semantically similar tasks → Mitigation: keep ranking deterministic for the first slice and leave embeddings/RAG as an explicit future option.
- Prompt context can grow too large → Mitigation: cap selected cases and rendered summary length.

## Migration Plan

- No database migration is required.
- Existing estimation behavior remains valid when no calibration catalog is present.
- Existing global/no-project estimation remains supported.
- Rollback is deleting or ignoring catalog files and disabling calibration-summary injection; persisted task records remain compatible.
