## Context

The token ledger already records total governed usage by category and stores provider/native evidence in `token_turns.raw_usage_json`. Recent Claude Code Worker runs demonstrated a confusing but legitimate shape: tiny fresh task input, large cache-read totals, visible cache-create totals, output tokens, and retry/failed attempts all rolled into one Worker execution number. OpenCode native usage can also report cache as `tokens.cache.read/write`, and Codex/OpenAI-compatible usage may report cached input under different detail fields.

The budget contract should remain conservative: if the provider reports cache tokens and cost as part of the run, the harness should keep those tokens in governed budget totals. The product gap is explanation and comparison, not suppressing spend evidence.

## Goals / Non-Goals

**Goals:**

- Normalize token component evidence from raw native/proxy usage into a provider-neutral shape for display and summaries.
- Preserve cache-inclusive total governed budget accounting.
- Split Worker execution display into completed task actuals versus failed/retry attempt spend where Worker Run status evidence is available.
- Render cache/fresh/output/reasoning/cost explanations on dashboard, board cards, and session/report surfaces before raw JSON.
- Support Claude Code and OpenCode evidence observed in the local DB, and add defensive Codex/OpenAI aliases for cached input fields.

**Non-Goals:**

- No Worker Adapter auth, launch, tracking-mode, or model-selection changes.
- No schema migration in the first slice; derive from existing raw usage and Worker Run/task/session records.
- No change to daily budget enforcement semantics: daily budget remains total governed model spend.
- No change to per-session Worker caps or task `actual_tokens`: both remain Worker execution scoped.
- No portal rewrite, SPA, websocket logging, or analytics warehouse.
- No claim that cache-inclusive token totals equal fresh prompt bloat or that cache should be excluded from provider spend.

## Decisions

1. **Derive normalized components from raw usage first, not a migration.**
   - Rationale: existing `raw_usage_json` contains Claude and OpenCode component fields, so the portal can explain recent confusing runs immediately.
   - Alternative considered: add normalized columns to `token_turns`. Rejected for first slice because it adds migration/backfill work before proving the display contract.

2. **Keep `total_tokens` and budget totals cache-inclusive.**
   - Rationale: Claude/OpenCode cache reads are provider-reported usage and can carry real cost. Excluding cache from budget would make governance less honest.
   - Alternative considered: show only fresh input + output as budget usage. Rejected because it hides provider spend and breaks budget-authoritative evidence.

3. **Display components as explanatory evidence, not a replacement total.**
   - Rationale: component evidence may be incomplete for older/proxy rows. The canonical budget total remains the ledger total; component rows explain why it is high when fields are available.
   - Alternative considered: recompute all totals from components. Rejected because provider totals may include reasoning or internal details not cleanly represented by all providers.

4. **Classify attempt status separately from token components.**
   - Rationale: cache-vs-fresh explains token shape, while completed-vs-failed/retry explains why dashboard Worker spend may exceed “Review N tasks.” These are different operator questions.
   - Alternative considered: only add cache split. Rejected because the reported demo also included failed/retry Worker attempts in the daily total.

5. **Use provider aliases in one normalization helper.**
   - Rationale: Claude, OpenCode, and Codex/OpenAI expose similar concepts under different keys. A single helper avoids scattering field-name rules through templates.
   - Initial aliases:
     - Claude: `input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `output_tokens`.
     - OpenCode: `tokens.input`, `tokens.cache.read`, `tokens.cache.write`, `tokens.output`, `tokens.reasoning`, plus equivalent `usage.cache` forms already persisted.
     - Codex/OpenAI defensive aliases: `cached_input_tokens`, `cached_tokens`, `input_token_details.cached_tokens`, `prompt_tokens_details.cached_tokens`, and output/reasoning aliases where present.

6. **Keep raw evidence available behind existing disclosure patterns.**
   - Rationale: operators need auditability, but raw JSON should not be the first thing needed to understand a budget spike.

## Risks / Trade-offs

- **Risk: Provider totals do not equal sum of displayed components.** → Mitigation: show ledger/provider total as authoritative and label component rows as “reported components”; include an “unclassified/other” delta when useful rather than forcing equality.
- **Risk: Codex emits a different cache shape than expected.** → Mitigation: keep raw evidence visible and add tests for supported aliases; treat unsupported fields as unavailable rather than wrong.
- **Risk: Retry spend display needs joins across sessions/tasks/Worker Runs.** → Mitigation: implement dashboard helpers with clear fallback to “attempt status unavailable” instead of blocking the cache explanation.
- **Risk: Operators misread cache reads as fresh context anyway.** → Mitigation: use blunt labels such as “cache read/reused context” and “fresh input/new prompt text,” not only provider field names.
- **Risk: Existing dirty worktree complicates verification.** → Mitigation: verify proposal-specific OpenSpec validation separately from broad repo tests and report unrelated failures if they occur.
