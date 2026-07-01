## Context

The Control Plane settings page already has a provider `<select>`, a native model `<select>`, preset buttons, and an explicit Custom model path. The previous Anthropic refresh made the curated list broader, but the list is still rendered as one flat dropdown, so the visible options do not reflect the selected provider.

The Control Plane model connection remains separate from Worker Adapter models. This change is only about the Control Plane settings form.

## Goals / Non-Goals

**Goals:**

- Filter visible curated model options by selected Control Plane provider.
- Keep native `<select>` behavior; no datalist/textarea/chip UI.
- Preserve OpenAI-compatible as Custom-only.
- Preserve saved non-curated or provider-incompatible values as Custom rather than silently rewriting them.
- Cover provider switching and saved-custom behavior with rendered portal tests.

**Non-Goals:**

- No provider API model discovery.
- No Worker Adapter discovery, allow-list, launch, or budget-accounting changes.
- No persistence/schema changes.
- No validation that rejects operator-entered Custom model IDs by provider.

## Decisions

1. Add provider metadata to curated model options.
   - Use one template-local curated list with provider, model, and label fields.
   - Rationale: keeps the small curated list in one place and avoids duplicating OpenAI/Anthropic arrays in JavaScript.
   - Alternative rejected: separate hardcoded selects per provider; more template duplication for the same model set.

2. Filter in the existing page JavaScript.
   - `syncControlPlaneModelControls()` should also read `control_plane_provider`, hide/disable incompatible options, and leave only provider-compatible curated options plus Custom.
   - The provider select should call the same sync function on change.
   - Rationale: the page is already server-rendered with small inline JavaScript for model/custom behavior.
   - Alternative rejected: add a backend route for filtered options; unnecessary for a static curated list.

3. Treat provider-incompatible saved curated IDs as Custom.
   - `current_model_is_curated` should be provider-aware, not model-only.
   - If the saved provider/model pair is not in the curated provider/model set, render Custom selected and preserve the saved value in `custom_control_plane_model`.
   - Rationale: avoids silently rewriting existing config while still making the visible curated list provider-correct.

4. Keep preset buttons explicit.
   - OpenAI preset buttons set provider `openai` and OpenAI models.
   - Anthropic preset button sets provider `anthropic` and `claude-haiku-4-5`.
   - OpenAI-compatible preset selects Custom and base URL entry.

## Risks / Trade-offs

- [Risk] Hidden disabled `<option>` behavior can vary by browser. → Mitigation: use both `hidden` and `disabled`, and test rendered attributes plus fallback Custom selection.
- [Risk] Provider switching could leave an incompatible selected model submitted. → Mitigation: sync function moves incompatible selections to Custom or first compatible option before submit.
- [Risk] Existing mismatched configs could look surprising. → Mitigation: preserve the saved value as Custom instead of auto-correcting it.
