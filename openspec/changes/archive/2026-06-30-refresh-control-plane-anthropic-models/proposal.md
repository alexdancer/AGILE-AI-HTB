## Why

The Control Plane model picker currently makes Anthropic feel artificially limited and includes a stale/provider-prefixed Sonnet option that does not match the direct Anthropic Messages API path. Operators need clear curated Anthropic choices plus the existing custom model escape hatch, without confusing this with Worker Adapter model discovery.

## What Changes

- Refresh the Control Plane model picker’s curated Anthropic options to current direct Anthropic API model IDs.
- Replace the stale `anthropic/claude-sonnet-4-20250514` option with direct Anthropic `claude-*` model IDs.
- Preserve the native dropdown plus explicit Custom model path for future/API-account-specific IDs.
- Keep provider API model discovery out of this slice; no runtime network call, cache, pagination, or failure UI.
- Keep Worker Adapter discovered/allowed model inventories separate and unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `control-plane-model-connection`: the curated Control Plane model choices must include current direct Anthropic API model IDs and must not present Worker/OpenRouter-style Anthropic IDs for the direct Anthropic provider.

## Impact

- Portal Control Plane settings template and tests.
- No database schema change.
- No new dependency.
- No Worker Adapter launch, discovery, allow-list, or budget-accounting behavior change.
