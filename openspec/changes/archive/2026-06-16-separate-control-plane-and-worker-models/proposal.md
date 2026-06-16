## Why

AGILE-AI-HTB is itself an agent harness and needs its own model connection for control-plane work, but local coding execution should run the user's chosen coding harness, such as OpenCode, Claude Code, or Codex, using that harness's own accessible models. The current local-runner design blends those concerns around `PROVIDER_API_KEY` and proxy-only verification, which makes OpenCode look like an OpenAI-style API client instead of a local coding harness that the board can launch, observe, budget, and report on.

## What Changes

- Separate the AGILE-AI-HTB control-plane model from Worker Harness model access in configuration, UI language, persistence, and launch flows.
- Add a control-plane model connection capability for task breakdown, estimates, model recommendations, summaries, and reports.
- Add native Worker Harness model discovery so adapters can list models available through OpenCode, Claude Code, Codex, or future harnesses instead of relying on static configured model IDs.
- Extend Worker Adapter verification to distinguish proxy-governed verification from native-usage verification.
- Allow local Worker launch readiness when a Worker Harness can be launched natively and its model usage can be imported or otherwise verified without routing through the Harness Proxy.
- Make budgeting visible across control-plane spend, Worker execution spend, and verification/overhead spend.
- Keep proxy-governed mode available as the strictest governance path, but stop treating it as the only valid local coding-harness path.

## Capabilities

### New Capabilities

- `control-plane-model-connection`: Configure, test, and use the model connection that powers AGILE-AI-HTB's own planning, estimation, recommendation, and reporting work.
- `native-worker-model-discovery`: Discover and persist models available from a local Worker Harness such as OpenCode, Claude Code, or Codex.

### Modified Capabilities

- `worker-adapter-verification`: Distinguish proxy-governed adapter verification from native Worker Harness verification and mark launch readiness based on the verified tracking mode.
- `local-execution-backend`: Run local coding harnesses through native adapter commands and expose native/proxy capability state for connected projects.
- `governed-worker-launch`: Launch local Worker Sessions with an explicit tracking mode and model selected from the verified adapter's discovered model set.
- `budgeted-launch-control`: Track and present budgets by spend category: control-plane, Worker execution, and verification/overhead.

## Impact

- Settings/config: replace confusing generic provider-key language with explicit control-plane model settings while preserving backward-compatible env behavior where practical.
- Portal: add clear setup sections for AGILE-AI-HTB model connection vs Worker Harnesses; show discovered Worker models and tracking mode.
- Persistence: store control-plane model connection status, discovered Worker models, adapter tracking mode, and spend category metadata.
- Adapters: add native discovery/usage paths, starting with OpenCode commands such as `opencode models`, `opencode run --format json`, `opencode stats`, and/or `opencode export`.
- Token ledger: record whether usage came from control-plane calls, proxy-governed Worker calls, native Worker usage import, or adapter verification.
- Launch guardrails: require a verified tracking mode and compatible discovered model before enabling Worker launch.
- Docs/demo: update local setup language so users understand they connect the AGILE-AI-HTB model separately from their coding harness.