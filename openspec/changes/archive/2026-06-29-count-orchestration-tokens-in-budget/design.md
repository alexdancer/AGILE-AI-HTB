## Context

Token usage is already persisted in a single token ledger with `usage_kind`, `raw_usage.spend_category`, and `raw_usage.usage_source`. The current dashboard reads two different concepts:

- total tracked tokens for the “Tokens Used” card; and
- `worker_execution` category tokens for the “Daily budget (Worker execution)” card and budget zone.

That split made sense when the daily budget was treated as Worker-only enforcement, but it now conflicts with the operator expectation that governed model spend includes control-plane/orchestration work. A live local check showed the concrete failure mode: 4,942 Agent Review tokens were recorded as `reporting_summary` / `control_plane`, the dashboard showed 4,942 tokens used, and the daily budget still showed `0 / 1,000,000`.

## Goals / Non-Goals

**Goals:**

- Make the daily token budget represent total governed model spend for the current budget period.
- Count Agent Review/reporting, estimation, task breakdown, adapter verification, and Worker execution token rows toward daily budget usage and zone calculation.
- Keep task `actual_tokens`, Worker session evidence, and estimation accuracy based on Worker execution only.
- Make dashboard and budget setup labels explain the distinction between total budgeted spend and Worker-only task actuals.
- Preserve the control-plane/orchestrator model vs Worker/coding harness model split.

**Non-Goals:**

- Do not move Agent Review into the Worker Adapter layer.
- Do not merge Agent Review tokens into task `actual_tokens`.
- Do not add a new budget table, schema migration, pricing model, or provider abstraction.
- Do not change Worker Adapter auth, discovered-model selection, tracking modes, or task lifecycle states.
- Do not redesign the portal or convert the server-rendered dashboard to a SPA.

## Decisions

1. **Use total token-ledger usage as daily budget consumption.**

   Daily consumed tokens should come from the current-period token ledger total, not only `by_category.worker_execution`. This treats any persisted token row as governed model spend unless future code explicitly introduces a non-budgeted ledger type. It also makes unknown `other` usage fail safe by counting toward the cap instead of disappearing from budget enforcement.

   Alternative considered: add a second “orchestration budget” and keep the existing Worker-only daily budget. Rejected for this slice because the user explicitly wants Agent Review/control-plane orchestration tokens included in the daily budget, not a separate informational budget.

2. **Keep Worker actuals Worker-only.**

   `task.actual_tokens` and Worker execution session summaries should still be based on `worker_execution` evidence. Agent Review/reporting tokens should appear as budgeted control-plane/orchestration spend, not as Worker execution output.

   Alternative considered: merge review tokens into the reviewed task’s actual token total. Rejected because it would corrupt Worker execution evidence and estimation accuracy.

3. **Use one daily budget gate for launch remaining capacity.**

   Worker launch guardrails should compare the task’s estimated Worker execution tokens against daily remaining capacity after subtracting all current-period governed spend. Per-session checks can remain Worker-estimate based because they cap a single Worker execution session, not all orchestration activity around it.

   Alternative considered: keep launch daily checks Worker-only while dashboard daily budget uses total spend. Rejected because it would reproduce the current “spent but not budgeted” confusion at launch time.

4. **Show category/source clarity instead of hiding categories.**

   The dashboard should make `reporting_summary` / Agent Review visible in the budget card or adjacent breakdown. Avoid labels like `control-plane 0` that only read `by_category.control_plane` while the same rows have `by_source.control_plane`. The useful operator scan is total used, Worker execution, review/reporting, planning/breakdown, setup/verification, and other.

## Risks / Trade-offs

- **Existing tests encode Worker-only daily budgets** → Update those tests to assert total governed spend consumes daily budget while Worker actuals remain Worker-only.
- **Control-plane-heavy review cycles may block a later Worker launch** → This is intended under the chosen semantics; the dashboard should make review/reporting spend visible enough that the operator understands why capacity changed.
- **Historical token rows categorized as `other` may now count toward budget** → Counting persisted token rows is safer than undercounting spend; expose `other` in the breakdown so it can be diagnosed.
- **Operator may still need Worker-only execution totals** → Keep Worker execution as a separate visible category and keep task/session actuals unchanged.
