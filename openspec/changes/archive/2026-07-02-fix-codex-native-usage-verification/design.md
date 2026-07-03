## Context

AGILE-AI-HTB separates the control-plane/orchestrator model from Worker/coding harness models. Codex is a Worker Adapter: a local Codex CLI integration that should be configured, verified, launched, and accounted for without treating the control-plane provider key as Worker auth.

Current diagnosis found Codex-specific gaps:

- The seeded/curated Codex inventory contained stale non-`gpt` IDs instead of the locally verified Worker model IDs `gpt-5.4` and `gpt-5.4-mini`.
- Codex is not considered `native_usage` capable, while OpenCode and Claude Code are.
- The inherited native command shape is OpenCode-like (`run --format json`) rather than Codex-like (`exec --json`).
- Codex documented JSONL usage appears on `turn.completed.usage` and can omit cost; the current parser rejects that shape.
- `observed_only` sentinel success can persist a generic `verified` status even though it is not budget-authoritative and must not be normal board-launch-ready.

## Goals / Non-Goals

**Goals:**

- Make Codex a first-class `native_usage` Worker Adapter using Codex CLI native auth/config.
- Use the exact Codex curated Worker model inventory: `gpt-5.4` and `gpt-5.4-mini`.
- Build Codex verification and launch commands with Codex-specific non-interactive JSONL semantics.
- Accept trustworthy Codex `turn.completed.usage` evidence for native usage accounting when bound to the launched run and selected model.
- Preserve raw provider token evidence, including cached input, while keeping normalized operator-facing actual/budget accounting aligned with the existing cache-read exclusion rule.
- Ensure verification/readiness surfaces distinguish budget-authoritative tracking from observed-only diagnostics.

**Non-Goals:**

- No control-plane/orchestrator model setting changes.
- No generic OpenAI/OpenRouter provider-key Worker Adapter.
- No Harness Proxy requirement for Codex native usage.
- No UI rewrite or new Worker setup flow beyond correcting labels/readiness where needed.
- No schema migration unless implementation proves existing evidence/config fields cannot represent the mode-specific state.
- No live Codex model catalog discovery; Codex inventory remains curated until a stable non-interactive discovery API is proven.

## Decisions

### Decision: Codex uses curated Worker model IDs exactly as Codex exposes them

Use `gpt-5.4` and `gpt-5.4-mini`. Treat previous placeholder/default values such as `5.3-codex-spark`, `5.4`, `5.4-mini`, `5.5`, `gpt-5.1-codex`, or `openai/gpt-4.1-mini` as stale unless a test intentionally uses them as historical parser data.

Alternative considered: keep non-`gpt` aliases. Rejected because live verification proved the local Codex CLI accepts `gpt-5.4` for native usage verification.

### Decision: Codex gets adapter-specific native command templates

Codex native verification and launch should use Codex non-interactive JSONL output:

```text
codex exec --json -m {model} {prompt}
```

Use the repo's existing command-plan redaction and template mechanisms, but do not reuse OpenCode's `opencode run --model ... --format json ...` assumptions for Codex.

Alternative considered: keep generic `NativeWorkerAdapterBuilder` defaults. Rejected because installed Codex CLI exposes `exec`, not `run`, so a generic default would verify the wrong interface.

### Decision: Codex native usage evidence is token-authoritative even when cost is absent

Codex documented JSONL emits `turn.completed` events with a `usage` object containing fields such as `input_tokens`, `cached_input_tokens`, `output_tokens`, and `reasoning_output_tokens`. Native usage evidence for Codex should require:

- zero exit status;
- a run/thread/session binding, such as a prior `thread.started.thread_id` in the same JSONL stream;
- the selected command model or an explicit matching model when emitted;
- non-zero token totals derivable from the usage payload;
- the verification sentinel for verification runs, or normal completion evidence for launch runs.

Cost is recorded when available but is not required for Codex native usage because Codex's documented JSONL sample does not include cost. This differs from Claude Code, where `total_cost_usd` / `modelUsage` is part of the trusted evidence shape.

Alternative considered: require cost for every native adapter. Rejected because it would make Codex impossible to verify despite providing token-complete native accounting.

### Decision: Cache-read tokens remain audit evidence but not normalized task actuals

Use the existing `token_usage_components` normalization direction: cache-read/reused context is preserved in raw evidence and component summaries but excluded from operator-facing task actuals and budget comparisons. Cache-write/create, fresh input, output, reasoning, and counted unclassified tokens remain normalized actuals.

### Decision: Verification status must be interpreted with tracking authority

Do not let `verification_status=verified` alone mean launch-ready. Readiness must require allowed models plus budget-authoritative verification evidence for `proxy_governed` or `native_usage`. `observed_only` may record diagnostic success, but it must remain non-authoritative and non-launchable from the normal board.

Alternative considered: rename/split the DB status immediately. Deferred; existing evidence fields may be enough if UI/readiness/guardrails consistently evaluate `tracking_mode` and `tracking_authoritative`.

## Risks / Trade-offs

- **Codex CLI flag drift** → Verify installed CLI help in tests/diagnostics where feasible and isolate Codex command construction in one adapter builder.
- **Codex JSONL shape changes** → Parser should be strict about authority but tolerant of aliases for token fields; tests should cover documented `turn.completed.usage`.
- **No cost in Codex output** → Budget token accounting remains authoritative; dollar-cost displays show unavailable unless Codex emits cost later.
- **Existing stale fixtures** → Update Codex-specific fixtures while leaving intentionally arbitrary model fixtures only when they are not asserting Codex inventory.
- **Generic `verified` wording confusion** → Readiness and UI copy must show the verified mode and authority, not just a single status badge.
