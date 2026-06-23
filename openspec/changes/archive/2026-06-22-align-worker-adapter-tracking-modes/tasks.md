## 1. Tracking Mode Domain Helpers

- [x] 1.1 Add shared tracking-mode helpers/constants for `proxy_governed`, `native_usage`, and `observed_only`, including canonical Portal labels, runtime-guardrail availability, accounting copy, and launchability metadata.
- [x] 1.2 Add or update unit tests for the helper mapping: proxy is runtime-governed, native is budget-authoritative after run, observed-only is not budget-authoritative.

## 2. Launch Guardrails

- [x] 2.1 Update `launch_guardrails.py` so Harness Proxy URL and session API key are required only when the verified tracking mode is `proxy_governed`.
- [x] 2.2 Ensure verified authoritative `native_usage` adapters can pass Launch Guardrails without proxy URL/session API key wiring when workdir/model/config checks pass.
- [x] 2.3 Ensure `observed_only`, missing tracking mode, or non-authoritative tracking evidence blocks normal AGILE Board launch with explicit reasons.
- [x] 2.4 Add targeted tests covering proxy-required, native-no-proxy, observed-only-blocked, unknown-mode-blocked, and unsupported-model cases.

## 3. Worker Adapter Verification and Native Evidence

- [x] 3.1 Make verification evidence consistently record tracking mode, tracking authority, selected model, usage source, sanitized command evidence, and run/session binding details.
- [x] 3.2 Tighten native usage parsing/validation so native evidence is authoritative only when machine-readable, model-aware, token-complete, exit-status-aware, and bound to the launched verification/run command.
- [x] 3.3 Ensure weak native evidence falls back to `observed_only` rather than `native_usage` launch-ready status.
- [x] 3.4 Preserve first-class OpenCode, Claude Code, Codex, and Hermes adapter presets and avoid replacing them with a generic provider-key adapter path.
- [x] 3.5 Add or update tests in `tests/test_worker_adapters.py` and `tests/test_worker_adapter_verification.py` for trustworthy native evidence, weak evidence fallback, proxy sentinel verification, and direct-proxy-call insufficiency.

## 4. Task Launch and Budget Override Behavior

- [x] 4.1 Ensure `task_launch.py` selects proxy launch commands only for `proxy_governed` and native launch commands only for `native_usage`, while preserving tracking mode and usage source on Worker Run metadata.
- [x] 4.2 Add support for native usage budget override acknowledgement when estimate exceeds remaining Worker budget, recording `budget_override=true` and the acknowledgement for audit.
- [x] 4.3 Ensure post-run native usage reconciliation can surface an overrun after imported usage is recorded.
- [x] 4.4 Add tests for native budget override acknowledgement, proxy budget override behavior, and observed-only no-board-launch behavior.

## 5. Portal and Worker Setup UI

- [x] 5.1 Update Worker Setup adapter view models/templates to show canonical tracking labels: `Governed via Harness Proxy`, `Tracked via Native Usage`, and `Observed Only`.
- [x] 5.2 Show launch readiness separately from runtime request guardrail availability and accounting authority on Worker Setup and board launch surfaces.
- [x] 5.3 Remove generic `Governed` copy for all launchable adapters; show runtime request guardrails as available only for proxy-governed adapters.
- [x] 5.4 Add or preserve Worker Setup diagnostic/test action semantics for observed-only adapters without setting Launch-ready or mutating AGILE Board task state.
- [x] 5.5 Add portal/template tests for tracking labels, observed-only diagnostic copy, native runtime-guardrail-not-available copy, and budget override acknowledgement copy.

## 6. Verification

- [x] 6.1 Run targeted tests for launch guardrails, Worker adapter verification, task launch, and Portal rendering.
- [x] 6.2 Run `openspec validate align-worker-adapter-tracking-modes --strict`.
- [x] 6.3 Run the broader `pytest` suite or document any blocker preventing the full suite from running.
