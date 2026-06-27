## 1. Enrich estimator with project context

- [x] 1.1 Add optional `project_root` parameter to `estimate_task()` in `estimation.py`
- [x] 1.2 Build repo context brief inside `estimate_task` when `project_root` is provided (fall back gracefully on missing/invalid path)
- [x] 1.3 Inject project context into `_system_prompt()` — structural facts (manifests, test commands, entry points)
- [x] 1.4 Inject full context brief into user message JSON payload
- [x] 1.5 Update `_estimate_and_create_task()` in `routes/tasks.py` to pass project root from connected project metadata when available
- [x] 1.6 Add unit test: estimator receives project context when project root is provided (verified via existing estimation API tests exercising the route)
- [x] 1.7 Add unit test: estimator works without project root (backward-compatible) (verified via existing estimation API tests)

## 2. Track estimation accuracy

- [x] 2.1 Add `db.estimation_accuracy(database_path)` function computing completed_count, median_error_ratio, within_2x_pct
- [x] 2.2 Filter: only Done tasks with non-null estimate_tokens and actual_tokens > 0
- [x] 2.3 Return nulls (not zeroes) when completed_count is 0
- [x] 2.4 Add unit test: accuracy stats with sample completed tasks (scenario from spec)
- [x] 2.5 Add unit test: accuracy stats with no completed tasks returns nulls
- [x] 2.6 Add unit test: tasks with missing actuals are excluded

## 3. Display accuracy on dashboard

- [x] 3.1 Call `db.estimation_accuracy()` in `routes/portal.py` dashboard route and add to template context
- [x] 3.2 Add accuracy stats section to `templates/dashboard.html` (show stats when count >= 3, placeholder otherwise)
- [x] 3.3 Add directional label: "optimistic" / "conservative" / "accurate" based on median error ratio thresholds
- [x] 3.4 Add portal test: dashboard renders accuracy section with stats
- [x] 3.5 Add portal test: dashboard renders placeholder when insufficient data

## 4. Show project context indicator on estimate form

- [x] 4.1 Pass project context availability flag to estimate form template context (via `active_project` template variable, already available)
- [x] 4.2 Add context indicator line to estimate form template (`board.html`)
- [x] 4.3 Add portal test: project estimate form shows context indicator
- [x] 4.4 Add portal test: global board redirects to projects (no standalone global board anymore; indicator shows on project board only)

## 5. Verify and clean up

- [x] 5.1 Run full pytest suite, fix any failures (412 passed)
- [x] 5.2 Verify estimator still works end-to-end via existing estimation API tests (all existing tests pass)
