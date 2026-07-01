## 1. Normalize Worker token components

- [x] 1.1 Update the shared native/proxy usage component helper to return normalized actual tokens, cache-read tokens, cache-write tokens, raw provider total, cost, and provider-total-only/unclassified evidence.
- [x] 1.2 Add/adjust unit tests for Claude Code, OpenCode, Codex/OpenAI cached-input aliases, Hermes/provider-total-only usage, missing component fields, and component sums that differ from provider totals.
- [x] 1.3 Ensure cache-write/cache-creation counts in normalized actuals and cache-read/reused-context does not.

## 2. Apply normalized actuals to budget and task reconciliation

- [x] 2.1 Update Worker Run/task actual reconciliation so `task.actual_tokens` uses normalized Worker actuals instead of cache-read-inclusive provider raw totals.
- [x] 2.2 Update daily launch budget and per-session Worker cap checks to compare against normalized governed spend while preserving raw provider totals as evidence.
- [x] 2.3 Keep control-plane/orchestration spend separate from Worker task actuals and exclude any reported cache-read component from budget-used calculations.
- [x] 2.4 Add/adjust budget and launch-guardrail tests for cache-heavy Worker usage, failed/retry attempts, and provider-total-only fallback behavior.

## 3. Update Portal evidence surfaces

- [x] 3.1 Update dashboard summaries to show normalized budget used, completed normalized Worker actuals, failed/retry normalized attempt spend, cache-read evidence, provider raw totals, and cost.
- [x] 3.2 Update session/report summaries to show normalized Worker actuals and cache-read/provider-raw evidence before raw usage JSON.
- [x] 3.3 Update board cards to show normalized actual tokens in compact metadata and keep cache-read/provider raw evidence available in compact details.
- [x] 3.4 Add/adjust portal tests for dashboard, session/report, and board card cache-heavy examples.

## 4. Apply ponytail prompt shaping to breakdown-created tasks

- [x] 4.1 Update Task Breakdown acceptance/prompt construction so implementation candidates keep objective, hard constraints, slice acceptance checks, required verification, expected response, and compact global contract only.
- [x] 4.2 Preserve full original source contract for Acceptance Verification candidates while avoiding implementation-slice prompt bloat.
- [x] 4.3 Add/adjust Task Breakdown tests proving unrelated sibling details and raw source prose are not repeated into every implementation prompt while hard constraints remain.

## 5. Verification

- [x] 5.1 Run `openspec validate normalize-worker-token-actuals --strict`.
- [x] 5.2 Run targeted tests for token components, budget/launch guardrails, portal evidence rendering, and Task Breakdown prompt shaping.
- [x] 5.3 Run `uv run pytest` and document any unrelated dirty-worktree/pre-existing failures separately.
