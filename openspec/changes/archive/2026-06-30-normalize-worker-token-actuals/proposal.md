## Why

Recent Claude Code Worker evidence showed that provider raw totals can be dominated by cache-read/reused-context tokens: four completed slices reported 2.44M raw provider tokens, but only about 149k non-cache-read task tokens. Operators need budget and task-actual numbers that reflect new Worker work while still preserving cache reads as audit evidence.

## What Changes

- Normalize Worker token accounting into task actuals, failed/retry actuals, cache-read evidence, provider raw totals, and cost.
- Exclude cache-read/reused-context tokens from task `actual_tokens`, launch budget comparisons, and operator-facing Worker actuals.
- Count cache-write/cache-creation tokens as task actuals because they represent newly processed context.
- Preserve cache reads and provider raw totals as auditable evidence on dashboard, board, and session/report surfaces.
- Keep completed Worker actuals separate from failed/retry Worker attempt spend.
- Apply the same provider-neutral component rule across Claude Code, OpenCode, Codex/OpenAI-style, and Hermes usage when fields exist; label unsupported totals as unclassified/provider-total-only instead of inventing splits.
- Add ponytail-style Worker prompt shaping for breakdown-created tasks: keep the task objective, hard constraints, slice-specific acceptance checks, required verification, and minimal global contract; avoid repeating unrelated source prose into every implementation slice.
- Do not change Worker Adapter auth, model discovery, tracking mode, launch command shape, or control-plane/Worker model responsibilities.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `token-budget-setup`: Daily/launch budget semantics and dashboard budget displays exclude cache-read tokens from budget-used/actual comparisons while preserving raw provider usage separately.
- `portal-evidence-readability`: Session/report summaries distinguish normalized task actuals from cache-read evidence and provider raw totals before raw JSON.
- `board-card-readability`: Board cards display normalized Worker actuals while keeping cache-read/provider raw evidence available in compact details.
- `task-breakdown-review`: Breakdown-created Worker prompts preserve ponytail-shaped slice context instead of repeating unnecessary global/source prose into every implementation task.

## Impact

- Affected code: native usage normalization/parsing, token ledger summary helpers, budget guardrail calculations, task actual reconciliation, dashboard/board/session view models and templates, Task Breakdown prompt/candidate shaping, and related tests.
- Data/API impact: no required schema migration for the first slice; derive normalized components from existing raw usage when possible and keep raw provider totals available.
- Budget semantics: cache-read tokens stop counting against task actuals and budget comparisons; cache-write/cache-creation, fresh input, output, reasoning, and unclassified authoritative totals still count when available.
- Dependencies: none expected.
