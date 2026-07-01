## 1. Calibration Catalog Data Model

- [x] 1.1 Add an estimation calibration module with a `CalibrationCase` shape covering case ID, task description, expected Worker-token range, complexity, task kind, recommended model, project profile metadata, optional actual Worker tokens, and rationale.
- [x] 1.2 Implement strict catalog loading/validation for checked-in/test catalog files, including clear errors for missing required fields, invalid ranges, duplicate IDs, and malformed project profile data.
- [x] 1.3 Implement lenient local catalog loading for `.htb/estimation_calibration.yaml` that ignores malformed cases, preserves valid cases, and returns sanitized warnings.
- [x] 1.4 Add a checked-in sample/default calibration catalog with non-secret DEMO-safe cases and schema comments or documentation.

## 2. Relevance Selection and Summary Rendering

- [x] 2.1 Implement deterministic relevance selection using structured filters for project profile, task kind, complexity, and recommended model where available.
- [x] 2.2 Add lexical overlap ranking against task descriptions with stable tie-breaking by case ID.
- [x] 2.3 Cap selected cases by count and rendered character length.
- [x] 2.4 Render selected cases into a bounded read-only calibration summary containing case IDs, expected token ranges, optional actual Worker tokens, and rationales.
- [x] 2.5 Preserve an internal seam for future SQL-derived completed-task calibration candidates without requiring live history for this implementation.

## 3. Estimator Integration

- [x] 3.1 Resolve calibration catalog sources for project-scoped estimation: checked-in/default catalog plus repo-local `.htb/estimation_calibration.yaml` when present.
- [x] 3.2 Include the bounded calibration summary in estimator input when relevant cases exist, alongside existing Repo Context Brief and budget numbers.
- [x] 3.3 Preserve existing behavior when no calibration catalog exists, when no cases match, when project root is unavailable, or when global estimation has no repo context.
- [x] 3.4 Ensure estimator output remains the only source of final `estimate_tokens`; do not add numeric multipliers, clamps, or post-processing based on catalog data.

## 4. Tests and Evals

- [x] 4.1 Add unit tests for strict catalog validation, duplicate/malformed cases, optional actual tokens, and expected range validation.
- [x] 4.2 Add unit tests for lenient local catalog behavior proving malformed local cases produce warnings while valid cases remain available.
- [x] 4.3 Add selection tests proving deterministic structured filtering, lexical ranking, stable tie-breaking, and selection caps.
- [x] 4.4 Add estimator prompt/API tests proving calibration summaries appear only when relevant and do not replace Repo Context Brief or budget payload fields.
- [x] 4.5 Add estimator eval coverage that checks catalog-backed estimate bands and reports case ID, expected range, and actual estimate on failure.
- [x] 4.6 Add regression coverage proving manual calibration cases do not inflate dashboard `completed_count` or merge Control Plane spend into Worker estimate accuracy.

## 5. Verification

- [x] 5.1 Run `openspec validate add-estimation-calibration-catalog --strict`.
- [x] 5.2 Run focused estimator/task-estimation tests: `uv run pytest tests/evals/test_estimator.py tests/api/test_task_estimation.py -q`.
- [x] 5.3 Run any new calibration-specific unit/eval test files added during implementation.
- [x] 5.4 Run the broader relevant pytest slice or full `uv run pytest` after implementation before marking OpenSpec tasks complete.
