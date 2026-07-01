## Context

The Control Plane model settings page already has the right shape: provider `<select>`, model `<select>`, custom model fallback, config-first save, runtime hot-swap, and stale `needs_test` evidence. The defect is the curated Anthropic list: it exposes only Haiku plus a stale `anthropic/...` Sonnet ID even though the direct Anthropic client posts to `/v1/messages` and expects first-party `claude-*` IDs.

Anthropic docs expose `GET /v1/models` and current model docs, but live model discovery would add network failure handling, pagination, caching, and a second setup status path. The existing custom model path already covers uncommon or future IDs.

## Goals / Non-Goals

**Goals:**

- Keep the existing native dropdown + Custom model UX.
- Refresh Anthropic curated Control Plane choices to direct Anthropic API IDs.
- Remove the stale/provider-prefixed Anthropic Sonnet option from curated choices.
- Preserve saved non-curated values through the Custom model path.
- Keep Control Plane model choices separate from Worker Adapter model inventories.

**Non-Goals:**

- No Anthropic `GET /v1/models` discovery UI in this slice.
- No persisted model catalog/cache.
- No database schema change.
- No Worker Adapter discovery, allow-list, launch, or tracking-mode change.
- No change to control-plane secret storage, connection testing, or budget accounting.

## Decisions

1. Curated list over live discovery for this slice.
   - Rationale: one template/test update fixes the operator pain. Live discovery adds failure UI and cache semantics for little gain while Custom model handles outliers.
   - Alternative considered: call Anthropic Models API from the settings page. Rejected for this slice due to extra network/state complexity.

2. Use direct Anthropic API IDs only for the Anthropic provider.
   - Rationale: `src/agile_ai_htb/llm.py` sends Anthropic requests to the first-party Messages API, so curated values should be `claude-*`, not OpenRouter-style `anthropic/...` IDs.
   - Initial curated Anthropic set: `claude-fable-5`, `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5`.
   - Alternative considered: keep older aliases for compatibility. Rejected for curated defaults; existing saved older values can remain Custom.

3. Preserve the single dropdown model control.
   - Rationale: the repo already fixed the datalist/textbox problem; this change only refreshes choices.
   - Alternative considered: provider-specific separate controls. Rejected as unnecessary.

## Risks / Trade-offs

- Curated Anthropic list can go stale → Custom model remains available; update the small list when docs change.
- Some accounts may not have access to every current model → explicit connection test remains the proof; save does not require network success.
- Existing configs using `anthropic/claude-sonnet-4-20250514` may become Custom on page load → preserve value rather than silently rewriting it.
