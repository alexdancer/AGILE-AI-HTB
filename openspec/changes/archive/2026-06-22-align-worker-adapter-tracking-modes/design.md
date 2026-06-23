## Context

AGILE-AI-HTB governs local coding-agent harnesses. A Worker Adapter is not a generic model-provider adapter; it is the integration that detects, configures, launches, and observes an installed CLI such as OpenCode, Claude Code, Codex, or Hermes.

The current code has pieces of the right model, but guardrails and UI can still drift into proxy-only assumptions. In particular, proxy URL/session-key wiring must be required for `proxy_governed`, not for verified `native_usage`, and `observed_only` must never look like a normal governed launch.

This design implements the tracking-mode contract captured in `CONTEXT.md` and the async Worker run lifecycle artifacts:

```text
Worker Adapter identity
  OpenCode / Claude Code / Codex / Hermes CLI integration

Tracking mode
  proxy_governed  -> proxy token rows + runtime request governance
  native_usage    -> machine-readable native usage + launch/review governance
  observed_only   -> diagnostics only, not AGILE Board launchable
```

## Goals / Non-Goals

**Goals:**

- Make `proxy_governed`, `native_usage`, and `observed_only` explicit implementation states.
- Allow verified authoritative `native_usage` launches without Harness Proxy URL/session API key wiring.
- Keep `observed_only` out of normal AGILE Board task launch while preserving a diagnostic/test flow.
- Validate native usage evidence before treating it as budget-authoritative.
- Display tracking-mode strength honestly in Worker Setup and board launch surfaces.
- Add tests that lock the distinction between adapter identity, tracking authority, runtime governance, and budget override behavior.

**Non-Goals:**

- Do not build new adapter families beyond the existing first-class adapter presets.
- Do not require all Workers to route through the Harness Proxy.
- Do not claim `native_usage` has runtime request guardrails.
- Do not introduce new provider-key fan-out, LiteLLM-only assumptions, or generic provider abstractions for Worker auth.
- Do not implement a full observed-only task execution path from the AGILE Board.

## Decisions

### Decision: Launch Guardrails branch by tracking mode

`launch_guardrails.py` should evaluate tracking mode as a first-class property from verification evidence:

- `proxy_governed`: requires verified authoritative tracking, supported model, valid workdir, session API key, and Harness Proxy URL.
- `native_usage`: requires verified authoritative tracking, supported model, valid workdir, and trustworthy native usage evidence metadata; it does not require proxy URL/session API key.
- `observed_only`: blocks normal governed task launch even if the command is callable.

Rationale: the guardrail is protecting launch truthfulness, not enforcing a single transport path.

Alternative rejected: keep requiring proxy URL/session key whenever tracking mode is missing or not proxy-governed. That preserves the old provider-wrapper assumption and blocks valid native CLI harnesses.

### Decision: Native usage evidence has a strict shape

Native usage becomes budget-authoritative only when machine-readable evidence includes:

- selected model
- prompt/input tokens
- completion/output tokens
- total tokens
- exit status
- command/session identifier or equivalent run-binding evidence

The evidence must bind to the Worker Run being launched or verified. Human-readable logs, approximate counts, missing model identity, or unbound usage fall back to `observed_only`.

Rationale: AGILE-AI-HTB can support native harness auth without overclaiming token accuracy.

Alternative rejected: scrape logs or accept approximate usage for demos. That would make the demo easier but weakens the product's token-governance claim.

### Decision: UI labels separate launch readiness from governance strength

Portal surfaces should map tracking modes to stable labels:

| Mode | Label | Runtime request guardrails | Accounting |
|---|---|---|---|
| `proxy_governed` | Governed via Harness Proxy | Available | Budget-authoritative during run |
| `native_usage` | Tracked via Native Usage | Not available | Budget-authoritative after run |
| `observed_only` | Observed Only | Not available | Not budget-authoritative |

The board and Worker Setup should not render a generic `Governed` badge for all launchable adapters.

Rationale: users need to understand what is enforced during the run versus reconciled after the run.

Alternative rejected: one launch-ready badge that hides the tracking mode. That blurs the distinction between proxy and native behavior.

### Decision: Observed-only is diagnostic-only

Observed-only adapters may run from Worker Setup diagnostics, not from normal AGILE Board task dispatch. Diagnostics can capture command start evidence, stdout/stderr, exit code or timeout, detected model when available, and a not-budget-authoritative warning.

Rationale: the AGILE Board is the product promise surface for governed token tracking.

Alternative rejected: allow observed-only board launches with a warning. That would make the board semantics ambiguous and undermine launch-readiness.

### Decision: Native usage budget overrides require explicit acknowledgement

When a `native_usage` task estimate exceeds remaining Worker budget, launch may proceed only through budget override with acknowledgement that native CLI calls cannot be request-throttled mid-run. The Worker Run records `budget_override=true` and the acknowledgement for audit.

Rationale: native usage is still budget-authoritative after reconciliation, but not request-governed during execution.

Alternative rejected: forbid native usage overrides entirely. That would be stricter than existing budget override semantics and unnecessarily blocks user-approved runs.

## Risks / Trade-offs

- Native CLI output formats may change → Keep parsing adapter-specific and fall back to `observed_only` when evidence no longer satisfies the strict shape.
- Existing tests may encode proxy-only assumptions → Update targeted launch guardrail, adapter verification, task launch, and portal tests together.
- UI copy may become verbose → Prefer compact labels with expandable details/advanced evidence.
- Existing adapter records may lack tracking-mode evidence → Treat missing or unknown tracking mode as not launchable until verification refreshes metadata.
- Native usage cannot stop overruns mid-run → Require explicit override acknowledgement and reconcile/alert after usage import.
