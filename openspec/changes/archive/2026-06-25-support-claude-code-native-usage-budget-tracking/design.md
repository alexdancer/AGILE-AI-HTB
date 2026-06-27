## Context

AGILE-AI-HTB already models Worker Adapter identity separately from tracking mode. Claude Code now proves that split matters: `claude models` can fail or be unavailable, while `claude -p --output-format json|stream-json --verbose` emits run-bound usage, model usage, `session_id`, and `total_cost_usd` for an explicitly selected model.

The existing native usage parser is shared by verification and task launch. That is the right place to fix accounting because both adapter verification and governed Worker Runs must consume the same evidence rules.

## Goals / Non-Goals

**Goals:**

- Verify Claude Code as `native_usage` when non-interactive Claude output contains sentinel text plus trustworthy usage/cost evidence.
- Record Claude cache read/creation tokens as prompt-side budget tokens so ledger totals match Claude Code cost evidence.
- Use Claude Code's native OAuth/config for Worker execution without requiring Harness Proxy credentials.
- Keep Claude model discovery independent from native usage verification.
- Preserve `observed_only`/failed verification when Claude output lacks run-bound usage/cost evidence.

**Non-Goals:**

- Do not implement proxy-governed Claude Code request throttling.
- Do not add a new model-discovery API for Claude Code.
- Do not add new provider credentials or store Claude OAuth secrets in AGILE-AI-HTB.
- Do not split Worker settings into separate webpages in this change.

## Decisions

### Use Claude Code result JSON as the authority

Use `claude -p --model {model} --output-format stream-json --verbose --max-budget-usd {cap} {prompt}` for native verification and launch. The final result object is authoritative when it includes `session_id`, `usage`, `modelUsage`, and `total_cost_usd`.

Alternative considered: require `claude models` or a separate discovery command before verification. Rejected because discovery is not usage proof and currently fails independently of successful usage-reporting runs.

### Count cache tokens as prompt-side budget tokens

For Claude Code result JSON, compute ledger fields as:

```text
prompt_tokens = input_tokens + cache_creation_input_tokens + cache_read_input_tokens
completion_tokens = output_tokens
total_tokens = prompt_tokens + completion_tokens
cost = total_cost_usd or modelUsage.<model>.costUSD
```

This preserves the existing token ledger shape while avoiding the undercount caused by recording only input/output tokens.

Alternative considered: store cache tokens only in `raw_usage` and leave `prompt_tokens` as `input_tokens`. Rejected because budget totals and alarms would undercount actual Claude usage.

### Keep one shared parser path

Extend `_parse_native_usage_evidence()` rather than adding a Claude-only call path. Verification and task launch already call this shared parser, so the smallest root-cause fix covers both surfaces.

Alternative considered: add a separate Claude verification path. Rejected because it would duplicate launch accounting logic and risk drift.

### `--max-budget-usd` is a safety cap, not proof

The CLI budget flag should be included where possible to bound accidental spend, but the Harness only treats the run as budget-authoritative after importing machine-readable usage/cost evidence.

Alternative considered: trust the CLI cap as budget compliance. Rejected because the Harness needs auditable ledger evidence and post-run reconciliation.

## Risks / Trade-offs

- Claude Code output schema may change → keep raw result JSON in `raw_usage` and test the observed schema with focused fixtures.
- Native usage cannot be throttled mid-run → keep existing native-usage acknowledgement/override semantics and label it as post-run accounting authority only.
- Cache token semantics differ from normal prompt tokens → store original cache fields in `raw_usage` while including them in prompt-side budget totals.
- Model aliases such as `sonnet` resolve to concrete models such as `claude-sonnet-4-6` → allow model binding through result `modelUsage`/assistant model evidence for the selected alias instead of requiring exact alias string equality when the CLI resolves it.
