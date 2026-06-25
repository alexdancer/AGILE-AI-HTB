## Context

The task estimator (`estimation.py:estimate_task`) currently receives only a task description string and raw budget numbers. It has no awareness of the project's language, framework, file structure, test commands, or repo-level instructions. The estimator prompt (`_system_prompt`) describes light routing policy from `guardrails.yaml` but no project surface. The confidence field is an LLM self-report with no calibration against actual Worker token consumption.

Meanwhile, `repo_context.py:build_repo_context_brief()` already walks the project tree and produces a compact brief (manifests, file sample, test commands, repo docs, secret-redacted excerpts) capped at 8,000 characters. This function is used for Worker prompts but not for estimator prompts.

The `tasks` table carries `estimate_tokens` and `actual_tokens` columns. These are populated but never compared programmatically. There is no dashboard section, route query, or template that shows estimation accuracy over time.

## Goals / Non-Goals

**Goals:**
- Pass compact project context (file tree, manifests, test commands, top-level structure, repo docs) into the estimator LLM call so estimates are grounded in actual project surface
- Compute simple accuracy stats (count, median error ratio, within-2x percentage) from completed tasks' estimate_tokens vs actual_tokens
- Display accuracy stats on the dashboard and indicate project context presence on the estimate form
- No new DB tables, no new dependencies, no change to confidence field semantics

**Non-Goals:**
- Feeding calibration data back into the estimator prompt (future step 3)
- Per-complexity or per-model accuracy breakdowns (can add later)
- Time-series accuracy charts
- Changing the confidence field to be anything other than an LLM self-report
- Enriching the task breakdown agent prompt (separate change)
- Historical accuracy persistence beyond live SQL queries on `tasks`

## Decisions

### 1. Estimator signature: optional `project_root` parameter

`estimate_task()` gains `project_root: str | None = None`. When non-None, `build_repo_context_brief(project_root)` runs and its rendered text is injected into both the system prompt and the user message. When None (no connected project, or estimation via global board), behavior is unchanged.

**Alternatives considered:**
- Always require project context → rejected. Estimation can happen without a connected project (global board, demo seed). Preserving the None path avoids breaking existing flows.
- Pass only to user message → rejected. System prompt needs to know it has context available to reason about.
- Build context in route and pass as string → rejected. Separation: `estimation.py` stays testable with or without file I/O.

### 2. Context injection shape

```
System prompt append:
"Project context: <manifests>, <test commands>, <entry points>"

User message context block:
{
  "task_description": "...",
  "remaining_daily_tokens": ...,
  "daily_cap_tokens": ...,
  "project_context": "<text from build_repo_context_brief()>"
}
```

The repo context brief text is already redacted for secrets by `repo_context.py`. The system prompt gets structural facts (what kind of project, how tested); the user message gets the full brief including file sample and doc excerpts.

**Alternative considered:** Only user message gets context → rejected. System prompt routing policy should reference language/framework when known.

### 3. Accuracy stats: live SQL, no precomputation

Two new read-only functions in `db.py`:
- `db.estimation_accuracy(database_path)` → returns `{completed_count, median_error_ratio, within_2x_pct}`
- Error ratio = `actual_tokens / estimate_tokens` (1.0 = perfect, >1 = underestimated, <1 = overestimated)
- Completed = `status = 'Done' AND estimate_tokens IS NOT NULL AND actual_tokens IS NOT NULL AND actual_tokens > 0`
- Only `Done` tasks counted. Review/Blocked tasks may have partial or unreliable actuals.

**Alternatives considered:**
- Precompute and store in `portal_settings` → rejected. Adds write path and staleness for ~3-row SQL result.
- Include Review tasks → rejected. Review tasks may have incomplete Worker Runs; actuals could be partial.

### 4. Accuracy display location

Dashboard `dashboard()` route already aggregates token totals, alarms, sessions, and next actions. Accuracy stats are added to the same template context dict. A small section at the bottom of `dashboard.html` renders count, median error ratio, and within-2x percentage.

Estimate form (`estimate_form` / `project_estimate_form`) adds a small context indicator line: "Estimating with project context: <project_name>" or "No project context — estimate will be less accurate."

**Alternative considered:** Separate `/analytics` page → rejected. Three numbers don't need a dedicated page.

### 5. No new template dependencies

Accuracy display uses existing CSS class conventions (`stat`, `k`, `v`) from base.html. No chart library, no new JS. Numbers only.

## Risks / Trade-offs

- **[Risk] Repo context brief adds ~2-8K chars to estimator prompt** → Mitigation: The brief is capped at 8,000 chars by `MAX_BRIEF_CHARS` in `repo_context.py`. Estimator is a control-plane model call charged as orchestration tokens — modest increase.
- **[Risk] Accuracy stats are meaningless with < 5 completed tasks** → Mitigation: Display "N/A — need more completed tasks" when count < 3.
- **[Risk] `actual_tokens` may be zero/null for tasks that never launched** → Mitigation: Filter `actual_tokens IS NOT NULL AND actual_tokens > 0` in query.
- **[Risk] Estimator may ignore project context** → Mitigation: This is an LLM quality issue, not a code issue. The calibration tracking (step 2) will reveal whether context helps. If accuracy doesn't improve, step 3 (few-shot calibration examples) is the next lever.

## Open Questions

None. Design is narrow and additive.
