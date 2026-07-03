## 1. Model inventory and adapter capability

- [x] 1.1 Update Codex seeded/curated Worker model inventory to exactly `gpt-5.4` and `gpt-5.4-mini` in production presets and Codex-specific tests.
- [x] 1.2 Treat previous Codex seeded defaults such as `5.3-codex-spark`, `5.4`, `5.4-mini`, `5.5`, `gpt-5.1-codex`, and `openai/gpt-4.1-mini` as unapproved stale defaults so they do not make Codex launch-ready.
- [x] 1.3 Mark Codex as `native_usage` capable only through Codex-specific command/evidence support, not through proxy-governed assumptions.
- [x] 1.4 Add tests that fail if Codex curated discovery invokes an unsupported model-listing command or returns stale non-`gpt` curated IDs.

## 2. Codex command construction

- [x] 2.1 Add or override Codex native verification command construction to use `codex exec --json -m {model} {prompt}` or the verified Codex-supported equivalent.
- [x] 2.2 Add or override Codex native launch command construction to use the same Codex non-interactive JSONL shape with the task prompt and selected allowed model.
- [x] 2.3 Add command-plan tests proving Codex does not use OpenCode-specific `run --format json` templates for verification or launch.
- [x] 2.4 Preserve existing redaction and command evidence behavior for Codex command plans.

## 3. Native usage parsing and accounting

- [x] 3.1 Add parser coverage for documented Codex JSONL streams containing `thread.started` and `turn.completed.usage` events.
- [x] 3.2 Extend native usage parsing to accept Codex `turn.completed.usage` when it is run-bound, token-complete, exit-status-aware, and tied to the selected command/model.
- [x] 3.3 Permit Codex native usage verification when token evidence is complete but dollar cost is absent; record cost as unavailable rather than failing solely on missing cost.
- [x] 3.4 Normalize Codex cache-read/cached-input evidence so raw provider totals are preserved while cache-read tokens are excluded from operator-facing task actuals and budget comparisons.
- [x] 3.5 Add negative tests for sentinel-only Codex output, unbound usage, nonzero exit, missing token totals, and model mismatch.

## 4. Verification and Worker Setup readiness

- [x] 4.1 Make Codex `native_usage` verification pass only when the sentinel and trustworthy Codex native usage evidence are both present.
- [x] 4.2 Ensure Codex `observed_only` verification can be recorded as diagnostic evidence but never as budget-authoritative or board-launch-ready.
- [x] 4.3 Update readiness evaluation and Worker Setup copy so Codex shows launch-ready only with allowed models and authoritative `native_usage` verification.
- [x] 4.4 Add portal/API route tests proving default verification mode errors are clear when unavailable, observed-only success is diagnostic-only, and native usage success is launch-ready.

## 5. Governed launch behavior

- [x] 5.1 Update Codex governed launch to use the Codex-specific native command path and selected allowed model.
- [x] 5.2 Reject discovered-but-disallowed or stale Codex model IDs before starting any Codex process.
- [x] 5.3 Record successful Codex native launch usage from `turn.completed.usage` as Worker execution evidence on the Worker/coding harness layer.
- [x] 5.4 Treat missing/untrusted Codex native usage after an otherwise launchable attempt as a recoverable Worker Run failure that returns the task to Estimated with sanitized evidence.
- [x] 5.5 Replace fake Codex-native test helpers with tests that exercise the real command/parser/readiness/launch path.

## 6. Verification

- [x] 6.1 Run targeted worker adapter, native usage parser, portal Worker Setup, and Codex launch tests.
- [x] 6.2 Run `openspec validate fix-codex-native-usage-verification --strict`.
- [x] 6.3 Run `uv run pytest` after implementation and record any pre-existing unrelated worktree/test failures separately.
