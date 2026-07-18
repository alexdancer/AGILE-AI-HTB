## Why

The dashboard "Budget spend breakdown" reports governed spend **by token count per category**,
but never in dollars — even though every `token_turns` row already stores a per-call `cost` and
the OpenRouter work now resolves a real `usage.cost`. Operators want to see the **actual USD cost
of the tokens they used**, split the same way the token breakdown already is.

The honest challenge is coverage: cost is only truthful for cost-reporting providers (OpenRouter)
and priced models. Everything else is genuinely unknown, so a naive dollar sum would show a
misleading `$0.00` for real-but-unpriced spend — the exact failure the connection-test UI already
forbids. This change adds a **coverage-aware** USD dimension that never fabricates a zero.

## What Changes

- Aggregate a USD dimension in the spend breakdown alongside the existing token `by_category`:
  `cost_by_category` (sum of resolved per-turn cost per category), `total_cost`, and a coverage
  signal (`priced_tokens` / `unpriced_tokens`) so the UI can report "N% priced."
- A category whose turns have tokens but no resolved cost reports its dollars as **null
  ("unpriced")**, never `$0.00`. Only turns with a known cost contribute dollars; their tokens
  count as priced, the rest as unpriced.
- Surface the USD figures in the dashboard "Budget spend breakdown": a dollar value beside each
  category's tokens, an "unpriced" label where a category has no known cost, a total, and a
  coverage line.
- Extend the bounded dashboard JSON projection to carry the new cost fields (fixed category keys,
  each a finite non-negative number or `null`; non-negative integer priced/unpriced token counts).
- Informational only — the daily/session **token** budget stays the sole enforcement authority;
  no USD cap, no change to zone computation or launch guardrails.

Non-goals: a USD spending cap or USD-based guardrails; maintaining/expanding the hard-coded price
table (that stays as-is — dollars come from the resolver); any Worker Adapter or token-counting
change; per-session or per-task USD rollups beyond the existing dashboard breakdown.

## Dependencies

- **`openrouter-control-plane-provider` (its Section 6):** makes `token_turns.cost` nullable and
  stops the `resolve_cost(...) or 0.0` masking, so "unknown" survives to aggregation as `null`.
  Coverage-aware honesty depends on that null-vs-zero distinction; this change consumes it and
  does not re-own the migration. If that work has not landed, this change is blocked on it.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `token-budget-setup`: the dashboard budget spend breakdown gains a coverage-aware USD cost
  dimension (dollars per category + total + priced/unpriced coverage), with unpriced spend shown
  as unavailable rather than `$0.00`. Enforcement remains token-based and unchanged.
- `react-portal-shell`: the bounded, authenticated dashboard JSON projection gains
  `cost_by_category` (the fixed category keys, each finite non-negative number or `null`),
  `total_cost` (finite non-negative number or `null`), and `priced_tokens` / `unpriced_tokens`
  (non-negative integers).

## Impact

- Code:
  - `src/foreman_ai_hq/db.py` — `_summarize_token_turns` (`:2019`) sums non-null `cost` per
    category into `cost_by_category`, accumulates `total_cost`, and counts `priced_tokens` /
    `unpriced_tokens`; `token_usage_breakdown` / `session_token_breakdown` carry the new keys.
  - `src/foreman_ai_hq/routes/portal.py` — dashboard builder (`:354`) surfaces the new fields
    into the `spend` object.
  - `frontend/src/views/Dashboard.jsx` — render USD per category + total + coverage in the
    "Budget spend breakdown" panel, with an "unpriced" label and no fabricated `$0.00`.
- Spec/projection: `react-portal-shell` dashboard JSON allowlist (`:524-528`) extended.
- Database: none new — reuses `token_turns.cost` (nullable via the dependency above).
- No USD budget cap; no Worker Adapter changes; no token-counting changes.
