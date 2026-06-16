## Context

AGILE-AI-HTB currently has two model-related responsibilities that are too tightly coupled in language and implementation:

1. The AGILE-AI-HTB control plane needs a model for orchestration work: task breakdown, estimation, recommendation, reports, summaries, and risk analysis.
2. The local execution backend needs to launch a user's preferred coding harness, such as OpenCode, Claude Code, or Codex, using the models that harness can already access.

The current implementation has a generic `PROVIDER_API_KEY` and a LiteLLM-backed Harness Proxy path. That is a valid strict-governance mode, but it is not the right default mental model for local coding harness execution. In local mode, the user expects the board to run their coding harness of choice, discover the models available to that harness, track tokens used by that harness, and compare actual usage against budget.

## Goals / Non-Goals

**Goals:**

- Introduce explicit control-plane model settings for AGILE-AI-HTB's own model usage.
- Keep control-plane model usage separate from Worker Harness model access and credentials.
- Discover Worker Harness models natively, starting with OpenCode.
- Support multiple Worker tracking modes:
  - proxy-governed usage through the Harness Proxy;
  - native usage imported from Worker Harness logs/stats/export;
  - observed-only launch as non-budget-authoritative when reliable usage is unavailable.
- Make launch readiness depend on verified tracking mode and compatible discovered model.
- Show budget and token spend by category: control-plane, Worker execution, and verification/overhead.
- Preserve proxy-governed mode as the strongest governance option without making it the only local path.

**Non-Goals:**

- Hosted runner, tunnel runner, or sandbox implementation.
- Full OAuth/provider-account management for every coding harness.
- Perfect mid-session enforcement for native Worker Harness mode.
- Replacing OpenCode, Claude Code, or Codex configuration systems.
- Implementing all adapters at the same depth in the first pass; OpenCode is the first native target.

## Decisions

### Decision: Treat AGILE-AI-HTB as a control-plane agent with its own model connection

AGILE-AI-HTB SHALL have an explicit control-plane model connection used for estimation, planning, summaries, and reports. Configuration and UI copy should use control-plane terms instead of generic provider-key terms.

Examples:

- `AGILE_AI_HTB_CONTROL_MODEL`
- `AGILE_AI_HTB_CONTROL_PROVIDER`
- `AGILE_AI_HTB_CONTROL_API_KEY`
- optional OpenAI-compatible base URL for local or hosted model endpoints

Backward-compatible env aliases may continue to work, but UI/docs should not teach `PROVIDER_API_KEY` as the primary concept.

Rationale: the harness itself needs model access, but that model is not the same thing as the coding harness's model.

### Decision: Worker Harness credentials/config remain native to each harness

OpenCode, Claude Code, Codex, and future coding harnesses should use their own installed CLI/config/auth for local native mode. AGILE-AI-HTB should not ask for an OpenAI-style key just because the selected Worker Harness is OpenCode.

Rationale: the local product promise is that the board runs the user's coding harness of choice. Forcing all local harnesses through LiteLLM first makes OpenCode look like a generic API client and breaks the user's expected workflow.

### Decision: Add explicit tracking modes

Each adapter verification result should declare a tracking mode:

- `proxy_governed`: Worker calls the Harness Proxy, and token usage is recorded directly by the proxy.
- `native_usage`: Worker uses native harness config, and AGILE-AI-HTB imports trustworthy usage from harness output, stats, export, or logs.
- `observed_only`: Worker can be launched, but usage is unavailable or insufficient for authoritative budget tracking.

Only `proxy_governed` and `native_usage` should be budget-authoritative and launch-ready for normal governed tasks. `observed_only` may be allowed for manual proof/spike flows but should not be presented as fully governed execution.

### Decision: OpenCode native discovery is the first concrete native adapter path

The OpenCode adapter should use installed CLI capabilities to discover models and usage. Candidate commands include:

- `opencode --version` for installation diagnostics;
- `opencode providers` for auth/config surface;
- `opencode models [provider]` for model discovery;
- `opencode run --model <provider/model> --format json ...` for non-interactive launch;
- `opencode stats` and/or `opencode export <sessionID>` for usage import.

The implementation should spike exact output formats before treating imported usage as budget-authoritative.

### Decision: Model recommendation must target discovered Worker models

Task estimation may still use the control-plane model, but the recommended coding model should be selected from the verified Worker Harness's discovered model list. If no Worker model has been discovered, tasks can be estimated but should remain analysis-ready rather than launch-ready.

Rationale: static YAML model routing cannot reflect what the selected local coding harness can actually access.

### Decision: Budget ledger stores spend category and source

Token usage rows should distinguish:

- `control_plane` for AGILE-AI-HTB's own model calls;
- `worker_execution` for coding harness sessions;
- `adapter_verification` for setup checks;
- `reporting` or `summarization` where useful.

Usage should also record source/tracking mode when possible: proxy-governed, native import, or manual/observed estimate.

Rationale: the user needs to know whether budget is being spent by the board, by the coding agent, or by verification overhead.

## Risks / Trade-offs

- Native OpenCode output may not expose stable per-session token usage → Start with a spike that captures real `opencode run --format json`, `opencode stats`, and `opencode export` output before marking `native_usage` verified.
- Native mode may not allow mid-request enforcement → Budget native Worker sessions at launch and reconcile actuals afterward; reserve mid-request enforcement for proxy-governed mode.
- Multiple adapters expose models/usage differently → Define a small adapter capability interface and let each adapter implement discovery and usage import separately.
- Backward compatibility with `PROVIDER_API_KEY` can keep confusing users → Preserve it only as a compatibility alias, while UI/docs present control-plane model settings as the primary setup.
- Model recommendation may recommend unavailable models if discovery is stale → Store discovery timestamps and show stale/failed discovery status in the Worker Harness UI.
- Usage import could double-count proxy-governed sessions if both proxy and native stats are read → Store tracking mode per session and only one authoritative usage source per session.

## Migration Plan

1. Add new control-plane model setting names while preserving existing env aliases.
2. Update Portal copy/docs to separate AGILE-AI-HTB model setup from Worker Harness setup.
3. Add adapter discovery data structures and OpenCode discovery command support.
4. Introduce tracking-mode fields for adapter verification and Worker sessions.
5. Update launch guardrails to require verified tracking mode and discovered model compatibility.
6. Update ledger/category views to expose control-plane vs Worker vs verification spend.

Rollback is straightforward because this is additive at the spec level: existing proxy-governed behavior can remain available while native discovery/tracking is introduced behind capability state checks.

## Open Questions

- Which OpenCode command provides the most reliable per-session usage evidence: JSON run events, `stats`, `export`, or a combination?
- Should control-plane model setup support local OpenAI-compatible endpoints in the first implementation pass?
- Should observed-only Worker launch be exposed in the UI, or reserved for tests/spikes only?
- How should model recommendation behave when multiple verified Worker Harnesses are available?
