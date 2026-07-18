## 1. Precondition

- [x] 1.1 Confirm the `openrouter-control-plane-provider` Section-6 work has landed: `token_turns.cost` is nullable and `resolve_cost(...)` results are stored without `None` → `0.0` coercion. If not, this change is blocked; do not duplicate that migration here.

## 2. Aggregation — `src/foreman_ai_hq/db.py`

- [x] 2.1 In `_summarize_token_turns` (`:2019`), in the existing loop, accumulate `cost_by_category` (sum of `turn.cost` per category when `cost is not None`), `total_cost` (sum of non-null costs), `priced_tokens`, and `unpriced_tokens` (a turn's tokens are priced iff its `cost is not None`).
- [x] 2.2 Return `cost_by_category` with the same fixed category keys as `by_category`, each value a float or `null` (`null` when the category has tracked tokens but no priced turn); `total_cost` a float or `null` (`null` only when no tracked turn has a resolved cost); `priced_tokens`/`unpriced_tokens` as ints whose sum equals `total_tokens`.
- [x] 2.3 Leave the Session Report path (`session_token_breakdown`) projection untouched — do not surface the new keys through its strict allowlist.

## 3. Dashboard data — `src/foreman_ai_hq/routes/portal.py`

- [x] 3.1 In the dashboard builder (`:354`), surface the new `cost_by_category`, `total_cost`, `priced_tokens`, `unpriced_tokens` from `token_usage_breakdown` into the `spend` object consumed by the dashboard JSON.

## 4. Dashboard render — `frontend/src/views/Dashboard.jsx`

- [x] 4.1 In the "Budget spend breakdown" panel (`:89`), render each category's USD cost beside its tokens: `$X.XXXX` when the category cost is a number, an explicit "unpriced" label when it is `null` (never `$0.00`).
- [x] 4.2 Render a `total_cost` line and a coverage line derived from `priced_tokens`/`unpriced_tokens` (e.g. "$0.86 · 62% of tokens priced"); when `total_cost` is `null`, show that no priced spend was recorded rather than `$0.00`.

## 5. Spec projection

- [x] 5.1 Ensure the dashboard JSON projection matches the `react-portal-shell` delta: `cost_by_category` fixed keys (finite non-negative number or `null`), `total_cost` (finite non-negative number or `null`), `priced_tokens`/`unpriced_tokens` (non-negative integers). No new fields leak into the Session Report projection.

## 6. Verification

- [x] 6.1 Unit: `_summarize_token_turns` with mixed turns (reported cost, computed cost, `null` cost) returns correct `cost_by_category` (null for all-unpriced categories), `total_cost`, and priced/unpriced token counts summing to `total_tokens`.
- [x] 6.2 Unit: a category with only `null`-cost turns reports cost `null`, never `0.0`; a category with a genuine `0.0` priced turn reports `0.0`.
- [x] 6.3 Frontend: the breakdown renders `$` per priced category, "unpriced" for null categories, and a coverage line; assert the dashboard JSON key allowlist includes the new fields and excludes them from the Session Report projection.
- [x] 6.4 Manual: dashboard with a real OpenRouter-backed run shows non-null category dollars + total; an Ollama/unpriced run shows "unpriced" and a coverage below 100%, no fabricated `$0.00`.
- [x] 6.5 Gates: `uv run pytest -q`, `npm --prefix frontend run check`, `openspec validate usd-spend-breakdown --strict`.
