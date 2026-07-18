## Context

The dashboard "Budget spend breakdown" (`Dashboard.jsx:89`) shows governed spend as token counts
per category. Its data comes from `db.token_usage_breakdown` → `_summarize_token_turns`
(`db.py:2019`), which today returns `{ total_tokens, by_category, by_source }` — tokens only. The
portal dashboard builder (`portal.py:354`) maps `by_category` into the `spend` object.

Every `token_turns` row already stores a per-call `cost` (`db.py` schema), and the OpenRouter work
made that cost truthful (`resolve_cost` prefers a reported `usage.cost`, else a computed price,
else `None`) and — in its Section 6 — makes the stored `cost` nullable so "unknown" is no longer
masked as `0.0`. This change consumes that: cost is only known for cost-reporting providers
(OpenRouter) and priced models; everything else is genuinely unknown.

`_summarize_token_turns` is shared by both the dashboard (`token_usage_breakdown`) and the Session
Report (`session_token_breakdown`). The Session Report JSON projection is strictly allowlisted
(`react-portal-shell:508,524-528`) and is out of scope here.

## Goals / Non-Goals

**Goals:**
- Add a coverage-aware USD dimension to the dashboard budget spend breakdown: dollars per
  category, total, and priced/unpriced coverage.
- Never fabricate `$0.00` for unknown cost — unpriced spend is labeled, matching the
  connection-test rule.
- Reuse the single existing summarizer and dashboard builder; no parallel computation.

**Non-Goals:**
- A USD spending cap or USD guardrails — token budget stays authoritative.
- Expanding/maintaining the hard-coded price table (dollars come from the resolver).
- Adding USD to the Session Report projection or any Worker Adapter / token-counting change.
- A new database column — reuses `token_turns.cost` (nullable via the dependency).

## Decisions

**1. Aggregate cost in the shared summarizer; expose it only in the dashboard projection.**
`_summarize_token_turns` gains three outputs derived in the same loop that already sums tokens:
`cost_by_category` (sum of non-null `cost` per category), `total_cost` (sum of non-null costs),
and `priced_tokens` / `unpriced_tokens` (a turn's tokens count as priced iff its `cost is not
None`). A category with tracked tokens but zero priced turns yields `null` (not `0.0`) for its
cost. The Session Report projection keeps its existing strict allowlist and does not surface these
new keys, so no Session Report spec change is needed.

**2. Coverage is token-weighted, reported as counts, not a float ratio.**
Expose `priced_tokens` / `unpriced_tokens` and let the UI derive "N% priced." Counts compose
cleanly across categories and avoid asserting a float precision contract in the projection.

**3. `null` means unpriced; `0.0` means genuinely priced at zero.**
This mirrors the connection-test "unavailable, never $0.00" rule at aggregate scale, and is only
honest because the dependency preserves `null` in `token_turns.cost`. A category cost is `null`
when it has tokens but no priced turn; `total_cost` is `null` only when no tracked spend has a
resolved cost at all.

**4. Dashboard render: USD beside tokens, explicit "unpriced" label, coverage line.**
`Dashboard.jsx` renders each category's dollars next to its tokens (`$X.XXXX`), an "unpriced"
label where the category cost is `null`, a total, and a coverage line ("$0.86 · 62% of tokens
priced"). No new panel — the existing "Budget spend breakdown" gains a column/line.

**5. Informational only.**
No change to `budgeted_token_usage`, zone computation, or launch guardrails — those stay on
normalized token spend. The USD fields are display-only.

## Risks / Trade-offs

- **Depends on the OpenRouter Section-6 de-masking.** If `token_turns.cost` is still `NOT NULL`
  with `0.0` coercion, coverage collapses (everything reads priced-at-zero). This change is
  blocked on that work and should not duplicate the migration.
- **Historical rows.** Turns written before the de-masking have `cost = 0.0` (ambiguous). They
  count as priced-at-zero, slightly overstating coverage for old windows. Acceptable — cost was
  not reliably tracked before; the default budget window is recent, limiting exposure.
- **Mixed provenance in one category.** A category can mix priced and unpriced turns; its dollar
  figure then reflects only the priced subset while its token count reflects all turns. The
  coverage line is what keeps this honest, so it must always render when any spend is unpriced.
- **Shared summarizer blast radius.** Adding keys to `_summarize_token_turns` touches a function
  the Session Report also calls; the mitigation is that projections are explicit allowlists, so
  the new keys only surface where a projection opts in (the dashboard).
