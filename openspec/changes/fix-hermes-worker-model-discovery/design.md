## Context

Worker model discovery currently uses a generic native command plan for most adapters: `{adapter_command} models`. That works for OpenCode, but Hermes Agent exposes model configuration through profile config/cache files and interactive commands, not a stable `hermes models` CLI. The live repro showed `hermes models` exits with argparse error code 2 before any auth/profile model issue matters.

The existing code already has the lazy pattern needed for this class of adapter: Claude Code curated discovery uses `SEEDED_WORKER_ADAPTER_MODELS`, records curated evidence, and preserves any operator-approved allowed subset.

## Goals / Non-Goals

**Goals:**

- Make Hermes Worker Adapter discovery produce a usable curated inventory without launching `hermes models`.
- Reuse the existing seeded model and allowed-model paths.
- Keep discovery evidence explicit that the source is curated, not native CLI output.
- Preserve OpenCode native discovery behavior and parser hardening.

**Non-Goals:**

- No parsing of Hermes private profile caches such as `provider_models_cache.json` or `cache/model_catalog.json`.
- No new Hermes CLI command, config file, dependency, or database schema.
- No change to Worker Adapter tracking modes, token accounting, native usage verification, or launch command shape.
- No automatic approval of curated models for governed launch.

## Decisions

- **Use curated Hermes inventory.** Add Hermes to the same curated-discovery branch as Claude Code, backed by `SEEDED_WORKER_ADAPTER_MODELS["hermes"]`. This is the smallest root-cause fix because the failure is an unsupported CLI command, not a parser problem.
  - Alternative: parse Hermes profile config and caches. Rejected for this slice because those files are private implementation details, can contain provider-specific shapes, and are unnecessary to unblock setup.
  - Alternative: add or require `hermes models`. Rejected because this repo should not depend on a new upstream Hermes command for the immediate operator path.

- **Preserve allowed subset semantics.** Curated discovery refreshes the discovered inventory but keeps `supported_models` empty unless the operator already configured allowed models. If an allowed subset exists, retain only models still present in the curated inventory.
  - Alternative: auto-allow all curated Hermes models. Rejected because discovery proves availability/options, not operator approval for governed launch.

- **Keep evidence source-specific.** Store `tracking_mode: "curated"` and a Hermes-specific `source` string so the UI/debug evidence does not imply native discovery succeeded.
  - Alternative: mark curated as native. Rejected because it hides the reason this path exists.

## Risks / Trade-offs

- Curated Hermes inventory can become stale → update `SEEDED_WORKER_ADAPTER_MODELS["hermes"]` when the supported Worker model defaults change.
- Operators with many Hermes-configured provider models will see only the curated first-slice inventory → add explicit cache/config parsing later only if real setup usage proves it is needed.
- A curated model may not be auth-ready in the local Hermes profile → verification/launch guardrails still prove execution separately before normal governed launch.
