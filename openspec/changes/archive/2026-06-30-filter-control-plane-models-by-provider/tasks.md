## 1. Provider-Aware Curated Models

- [x] 1.1 Update `src/agile_ai_htb/templates/control_plane.html` curated model data to include provider metadata for each first-party model.
- [x] 1.2 Make `current_model_is_curated` provider-aware so mismatched saved provider/model pairs render through Custom.
- [x] 1.3 Keep OpenAI-compatible on the Custom model path without exposing first-party curated model choices as compatible selections.

## 2. Dropdown Filtering Behavior

- [x] 2.1 Update the provider selector to resync model options whenever the provider changes.
- [x] 2.2 Update `syncControlPlaneModelControls()` to hide/disable model options that do not match the selected provider.
- [x] 2.3 Ensure preset buttons still set valid provider/model pairs and preserve the Anthropic cheap/default preset.

## 3. Tests

- [x] 3.1 Add rendered-template assertions that OpenAI-selected settings expose only OpenAI curated choices as selectable options.
- [x] 3.2 Add rendered-template assertions that Anthropic-selected settings expose only `claude-*` curated choices as selectable options.
- [x] 3.3 Add coverage that OpenAI-compatible and provider-incompatible saved models preserve the Custom model value.

## 4. Verification

- [x] 4.1 Run targeted Control Plane portal tests.
- [x] 4.2 Run `openspec validate filter-control-plane-models-by-provider --strict`.
- [x] 4.3 Run `uv run pytest` after implementation, unless blocked by unrelated dirty-worktree failures and reported with evidence.
