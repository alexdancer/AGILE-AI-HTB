## Why

A simple Claude Code demo showed over 2.7M Worker execution tokens for four tasks, which looked impossible until the raw evidence showed that most tokens were provider-reported cache reads and that failed/retry attempts were included in the daily total. Operators need the budget to remain auditable and cache-inclusive, but the portal must explain the total instead of presenting cache/retry spend as an opaque "task actuals" number.

## What Changes

- Add a provider-neutral token component breakdown for Worker/native usage evidence: fresh input, cache read, cache write/create, output, reasoning, total, and cost when available.
- Keep daily governed budget usage cache-inclusive and retry-inclusive because those tokens are provider-reported spend evidence.
- Update dashboard budget/Worker panels to separate total governed spend, Worker execution spend, completed-task Worker actuals, failed/retry Worker spend, and token component composition.
- Update session/report and board evidence surfaces so task actuals remain Worker-only while cache-heavy totals show an explanatory split before raw JSON/logs.
- Add Codex/OpenAI cache aliases defensively while preserving existing Claude Code and OpenCode native usage accounting.
- Do not change Worker Adapter authentication, model selection, launch flow, or control-plane/Worker model responsibilities.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `token-budget-setup`: dashboard and daily budget displays explain cache-inclusive governed spend, Worker execution spend, completed task actuals, failed/retry spend, and token component composition.
- `portal-evidence-readability`: session and Worker report summaries show token component splits before raw usage evidence when raw native usage contains cache/output/reasoning details.
- `board-card-readability`: board cards show actual Worker execution tokens with a compact cache/fresh/output explanation when component evidence exists, without merging control-plane/reporting spend into task actuals.

## Impact

- Affected code: native usage normalization/parsing, token ledger summary helpers, dashboard view model/template, session/report evidence view models/templates, board card view models/templates, and related portal/worker tests.
- Data/API impact: no required schema migration for the first slice; derive components from existing `token_turns.raw_usage_json` where possible and fall back cleanly when raw component evidence is unavailable.
- Budget semantics: daily governed budget remains total governed model spend; per-session Worker caps and task `actual_tokens` remain Worker execution scoped.
- Dependencies: none expected.
