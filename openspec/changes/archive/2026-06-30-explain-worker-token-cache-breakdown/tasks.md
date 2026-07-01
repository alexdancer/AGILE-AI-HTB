## 1. Usage Component Normalization

- [x] 1.1 Add a provider-neutral token component helper that derives fresh input, cache read, cache write/create, output, reasoning, cost, total, and unclassified tokens from existing token ledger raw usage.
- [x] 1.2 Support Claude Code aliases (`input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `output_tokens`) and preserve cache-inclusive prompt/total accounting.
- [x] 1.3 Support OpenCode aliases (`tokens.input`, `tokens.cache.read`, `tokens.cache.write`, `tokens.output`, `tokens.reasoning`, and persisted `usage.cache` equivalents).
- [x] 1.4 Add defensive Codex/OpenAI cached-input aliases (`cached_input_tokens`, `cached_tokens`, `input_token_details.cached_tokens`, `prompt_tokens_details.cached_tokens`) without inventing cache write/create when absent.
- [x] 1.5 Add unit tests for Claude, OpenCode, Codex/OpenAI alias shapes, missing component evidence, and component sums that differ from provider totals.

## 2. Dashboard Budget Explanation

- [x] 2.1 Extend token budget/dashboard summary helpers to expose Worker execution component totals for the current budget period while keeping total governed spend cache-inclusive.
- [x] 2.2 Add completed Worker actuals versus failed/retry/unknown attempt spend classification where Worker Run/task status joins are available.
- [x] 2.3 Update the dashboard view model and template to show total governed spend, Worker execution spend, completed task actuals, failed/retry spend, and cache/fresh/output/reasoning/cost composition with unavailable states.
- [x] 2.4 Add portal tests proving cache-heavy Worker spend is explained, failed/retry spend remains budgeted but separate, and missing component/status evidence does not fabricate zeros.

## 3. Session, Report, and Board Evidence

- [x] 3.1 Update session/report evidence summaries to render token component breakdowns before raw usage JSON for Claude Code, OpenCode, and Codex/OpenAI-style cached input evidence.
- [x] 3.2 Ensure session/report displays keep provider or ledger total tokens authoritative when component totals are partial or do not sum exactly.
- [x] 3.3 Update board card view models/templates to keep actual Worker tokens visible and add concise component explanation when task Worker Run evidence exists.
- [x] 3.4 Add session/report and board tests proving task actuals remain Worker-only and control-plane estimation, task breakdown, and Agent Review tokens are not merged into task actuals.

## 4. Verification

- [x] 4.1 Run focused unit tests for usage component normalization.
- [x] 4.2 Run focused portal tests for dashboard, session/report evidence, and board card displays.
- [x] 4.3 Run `openspec validate explain-worker-token-cache-breakdown --strict`.
- [x] 4.4 Run `uv run pytest` and report any failures separately from pre-existing dirty-worktree changes.
