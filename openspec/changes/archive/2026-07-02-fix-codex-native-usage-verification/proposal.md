## Why

Codex Worker Adapter setup currently has three coupled correctness gaps: the curated model inventory uses stale/wrong IDs, Codex is not treated as a native-usage-capable Worker like OpenCode, and verification can mark sentinel-only observed runs as `verified` without proving budget-authoritative usage. This undermines the harness claim that normal AGILE Board launches are governed by verified tracking evidence.

## What Changes

- Correct Codex curated Worker model inventory to the actual locally verified Codex model IDs: `gpt-5.4` and `gpt-5.4-mini`.
- Treat Codex as a first-class `native_usage` Worker Adapter when verified through Codex-specific non-interactive JSONL output.
- Add Codex-specific native verification and launch command semantics based on `codex exec --json -m {model} ...`, rather than OpenCode-shaped `run --format json` assumptions.
- Extend native usage evidence handling to accept Codex `turn.completed.usage` JSONL when it is run-bound, token-complete, exit-status-aware, and tied to the selected command/model.
- Tighten Worker Adapter verification semantics so each verification result proves the requested tracking mode:
  - `proxy_governed` requires proxy token evidence.
  - `native_usage` requires trustworthy machine-readable native usage evidence.
  - `observed_only` remains diagnostic-only and never implies normal board-launch readiness.
- Replace fake Codex-native readiness helpers in tests with coverage that exercises the real Codex model inventory, command construction, verification, parser, readiness, and launch guardrails.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `native-worker-model-discovery`: Codex curated discovery must expose the exact supported Codex Worker model IDs and keep discovery separate from allowed-model selection and tracking verification.
- `worker-adapter-verification`: Codex must be verifiable in `native_usage` mode using trustworthy Codex JSONL usage evidence, and observed-only sentinel success must not be recorded as budget-authoritative verification.
- `governed-worker-launch`: Codex native Worker launches must use a Codex-specific non-interactive command shape and must fail recoverably when native usage evidence is missing or untrusted.
- `guided-worker-setup`: Worker Setup readiness and verification UI must distinguish diagnostic observed-only success from budget-authoritative native usage verification for Codex.

## Impact

- Affected code areas: Worker Adapter presets and model allow-listing, Codex adapter command builders, native usage parsing/normalization, adapter verification, Worker Setup readiness, launch guardrails, and task launch usage import.
- Affected tests: Worker adapter discovery/configuration tests, native usage parser tests, adapter verification route tests, Worker Setup readiness tests, and governed launch tests for Codex.
- No new external service dependency is introduced.
- No control-plane/orchestrator provider settings change; Codex remains a Worker/coding harness adapter using native Codex CLI auth/config.
- No schema migration is expected unless implementation proves existing verification evidence cannot express mode-specific readiness cleanly.
