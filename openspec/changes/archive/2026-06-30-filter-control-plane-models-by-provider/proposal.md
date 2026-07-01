## Why

The Control Plane settings form currently shows every curated model in one dropdown, so provider `openai` can visually offer Claude models and provider `anthropic` can visually offer OpenAI models. That weakens the provider/model contract and makes the refreshed curated model list easier to misuse.

## What Changes

- Filter the native Control Plane model dropdown by selected provider.
- Show OpenAI models only when provider `openai` is selected.
- Show Anthropic `claude-*` models only when provider `anthropic` is selected.
- Keep `openai-compatible` on the explicit Custom model path instead of presenting first-party provider presets as compatible choices.
- Preserve existing non-curated saved models through the Custom model path.
- Keep Worker Adapter model discovery/allow-lists separate and unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `control-plane-model-connection`: the Control Plane provider selection must constrain visible curated model choices to models compatible with that selected provider while preserving the Custom model escape hatch.

## Impact

- Portal Control Plane settings template and JavaScript.
- Portal tests for model settings and custom model preservation.
- No database schema change.
- No new dependency.
- No Worker Adapter launch, discovery, allow-list, or budget-accounting behavior change.
