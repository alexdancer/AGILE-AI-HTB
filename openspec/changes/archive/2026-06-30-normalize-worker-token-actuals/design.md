## Context

The current token ledger stores provider/native usage totals and raw evidence in `token_turns.raw_usage_json`. Existing cache-breakdown work made cache-heavy provider totals visible, but the current product contract still treats cache-read tokens as budgeted Worker spend. Recent Claude Code evidence showed why that is misleading: four completed Worker slices reported 2.44M provider raw tokens, while the non-cache-read work was about 149k. The same run also showed failed/retry attempts need their own bucket.

The control-plane/orchestrator model remains separate from Worker/coding harness models. This change only normalizes Worker usage evidence and Worker prompt shape; it does not change Worker Adapter auth, model discovery, tracking modes, or launch command templates.

## Goals / Non-Goals

**Goals:**

- Define one provider-neutral normalized Worker actual formula: fresh input + cache write/create + output + reasoning, excluding cache read/reused context.
- Preserve raw provider total tokens, cache-read tokens, cost, and raw JSON as audit evidence.
- Use normalized Worker actuals for task `actual_tokens`, completed-task actual summaries, launch budget comparisons, and per-session Worker budget comparisons.
- Show failed/retry normalized actuals separately from completed task actuals.
- Support Claude Code, OpenCode, Codex/OpenAI-compatible, and Hermes usage shapes without inventing missing component values.
- Apply ponytail-style prompt shaping to breakdown-created tasks so implementation slices receive the smallest honest prompt that still preserves hard constraints and verification.

**Non-Goals:**

- No schema migration in the first slice unless implementation proves existing raw usage cannot support required displays.
- No Worker Adapter auth, launch, tracking-mode, model-discovery, or model-selection changes.
- No portal rewrite or analytics warehouse.
- No claim that HTB always uses fewer tokens than direct coding agents.
- No weakening of acceptance criteria, synthetic-data guardrails, no-secret rules, required verification, or final Acceptance Verification behavior.

## Decisions

1. **Normalize task actuals by excluding only cache reads.**
   - Formula: `normalized_actual_tokens = fresh_input + cache_write + output + reasoning + unclassified_counted_tokens`.
   - Cache read/reused context is recorded separately and excluded from budget/actual comparisons.
   - Cache write/cache creation counts because it represents newly processed context for the run.
   - Alternative considered: exclude all cache tokens. Rejected because it makes large initial context creation look artificially cheap.

2. **Keep raw provider total as evidence, not the operator budget number.**
   - `raw_provider_total_tokens` remains visible in details and summary explanations.
   - Dashboard/board/session copy should lead with normalized actuals and show cache-read/raw total as explanatory evidence.
   - Alternative considered: keep raw total as the daily budget number and only add copy. Rejected because it still makes cache reuse look like budget burn.

3. **Use existing raw usage JSON first.**
   - Existing `token_turns.raw_usage_json` already contains Claude/OpenCode-style component fields.
   - A helper can derive normalized components at read/reconciliation time and tests can pin provider aliases.
   - Alternative considered: add normalized columns and backfill immediately. Rejected for the first slice as unnecessary unless query complexity or performance proves it.

4. **Classify attempts separately from components.**
   - Completed Worker actuals answer “what did accepted/reviewable tasks cost?”
   - Failed/retry actuals answer “what was wasted before success?”
   - Cache-read evidence answers “why is provider raw total huge?”

5. **Fail closed on unknown component shapes.**
   - If provider evidence exposes a total but not cache components, label it `provider-total-only` or `unclassified` and count it according to the existing authoritative total rather than fabricating zeros.
   - Codex/OpenAI cached-input aliases should be recognized when present, but missing cache-write fields should remain unavailable.

6. **Use ponytail prompt shaping where the Harness creates Worker task text.**
   - Implementation tasks from breakdown review should receive objective, hard constraints, slice acceptance checks, required verification, minimal global contract, and expected response.
   - Acceptance Verification tasks still receive enough original source contract to verify the integrated artifact.
   - Alternative considered: prompt-compress every Worker launch. Rejected because manual tasks may already be concise and aggressive compression risks losing user intent.

## Risks / Trade-offs

- **Risk: Some providers report only total tokens.** → Mitigation: label as provider-total-only/unclassified and keep raw evidence visible; do not invent cache splits.
- **Risk: Excluding cache reads hides real provider cost.** → Mitigation: show provider cost, raw provider total, and cache read evidence separately; cost budgets can still use cost when available.
- **Risk: Existing tests expect cache-inclusive daily budget totals.** → Mitigation: update affected budget/dashboard tests to assert normalized budget usage plus separate raw provider evidence.
- **Risk: Prompt shaping could remove important constraints.** → Mitigation: never drop hard constraints, synthetic-data rules, no-secret/no-network rules, required verification, or Acceptance Verification source contract.
- **Risk: Existing dirty worktree complicates broad verification.** → Mitigation: validate this OpenSpec change directly and report broad test failures separately if they are caused by unrelated current worktree state.
