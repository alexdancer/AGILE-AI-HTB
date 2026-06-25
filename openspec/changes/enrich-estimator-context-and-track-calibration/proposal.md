## Why

The task estimator LLM produces token estimates with zero project context (no file tree, no language/framework detection, no test commands) and a self-reported confidence score that is never calibrated against actual Worker token usage. Estimates are blind guesses; confidence is ungrounded. Without project context and accuracy tracking, estimation cannot improve, Spike has no meaningful trigger signal, and operators cannot tell whether estimates are getting better or worse.

## What Changes

- **Step 1 — Enrich estimator prompt with project context**: Pass `build_repo_context_brief()` output (file tree, manifests, test commands, entry points, repo docs) into the estimator LLM call so it has concrete project surface to inform its token estimate, complexity classification, and model recommendation.

- **Step 2 — Track estimation accuracy**: Record each task's estimated tokens vs actual Worker tokens on completion. Expose a minimal accuracy summary (count of completed tasks, median error ratio, within-2x percentage) on the dashboard and estimator form so operators can judge whether estimation is trustworthy.

- **No new DB tables**: Accuracy stats are computed from existing `tasks` rows (`estimate_tokens`, `actual_tokens`) and `token_turns` usage data. Context enrichment reuses `repo_context.build_repo_context_brief()` which already exists.

- **No change to confidence semantics**: The confidence field remains an LLM self-report. Step 2 adds external calibration data; step 3 (future) can feed it back into the prompt. This change is the foundation.

## Capabilities

### New Capabilities

- `estimator-project-context`: The estimator LLM receives a compact project context brief (manifests, file sample, test commands, repo docs) alongside the task description and budget numbers.

- `estimation-accuracy-tracking`: Completed tasks are compared against their estimates; aggregate accuracy metrics are computed and displayed.

### Modified Capabilities

None. This is additive — no existing spec requirements change.

## Impact

- `src/agile_ai_htb/estimation.py`: `estimate_task()` signature gains an optional `project_root` parameter; `_system_prompt()` accepts a context brief string; user message enriched with project context.
- `src/agile_ai_htb/routes/tasks.py`: `_estimate_and_create_task()` passes project context when a connected project exists.
- `src/agile_ai_htb/db.py`: New query functions for accuracy stats (read-only, existing columns).
- `src/agile_ai_htb/routes/portal.py`: Dashboard template includes accuracy summary; estimate form shows project context indicator.
- `src/agile_ai_htb/templates/dashboard.html`: Accuracy stats section added.
