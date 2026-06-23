## Why

Worker Adapter implementation and UI still risk treating local coding-agent CLIs as proxy-only provider integrations. The product needs implementation behavior that matches the clarified model: adapters launch real local harness CLIs, while token authority and runtime governance are determined by explicit tracking modes.

## What Changes

- Align Launch Guardrails with tracking modes:
  - `proxy_governed` requires Harness Proxy URL and session API key.
  - `native_usage` is launchable without proxy wiring only when verified as budget-authoritative.
  - `observed_only` is blocked from normal AGILE Board launches.
- Make tracking-mode metadata and evidence first-class in Worker Adapter verification and launch paths.
- Validate `native_usage` evidence as machine-readable, model-aware, token-complete, exit-status-aware, and bound to the launched Worker Run.
- Update Portal/board labels so launch readiness, tracking label, runtime request guardrails, and accounting authority are displayed separately.
- Require explicit acknowledgement for `native_usage` budget overrides because native CLI calls cannot be request-throttled mid-run.
- Preserve first-class named adapters for OpenCode, Claude Code, Codex, and Hermes instead of collapsing them into a generic provider-key flow.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `governed-worker-launch`: Tracking modes control launchability, proxy requirements, native usage authority, observed-only blocking, and runtime governance labels.
- `worker-adapter-verification`: Adapter verification must record tracking mode, tracking authority, and trustworthy native usage evidence requirements.
- `board-launch-selection`: Board/Portal launch controls must show tracking-mode-specific copy and require `native_usage` budget-override acknowledgement.
- `adapter-configuration-ui`: Worker Setup must display canonical tracking labels and allow observed-only diagnostics without showing Launch-ready.

## Impact

- Code: `src/agile_ai_htb/launch_guardrails.py`, `src/agile_ai_htb/worker_adapters.py`, `src/agile_ai_htb/task_launch.py`, Portal routes/templates that render Worker Setup and board launch forms.
- Tests: worker adapter verification, launch guardrails, task launch, portal/board rendering, and budget override behavior.
- Docs/OpenSpec: implements the clarified Worker Adapter tracking-mode contract already captured in `CONTEXT.md` and the async Worker run lifecycle design.
- No new external dependencies expected.
