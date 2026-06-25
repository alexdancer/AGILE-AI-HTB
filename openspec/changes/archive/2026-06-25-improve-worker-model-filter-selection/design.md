## Context

Worker Setup already separates Worker Adapter discovered models from the operator-approved allowed subset. The backend route accepts `allowed_models` checkbox values, validates them against discovered models, and saves the subset where estimate, board selection, readiness, and launch guardrails already read it.

The pain is UI-only: long OpenCode model inventories make manual checkbox selection slow.

## Goals / Non-Goals

**Goals:**
- Make long discovered Worker model lists faster to curate.
- Preserve the existing `allowed_models` form contract and backend validation.
- Keep the control-plane/orchestrator model separate from Worker/coding harness model selection.
- Use plain HTML/CSS/JavaScript with no dependency or schema changes.

**Non-Goals:**
- Add model presets, provider wildcards, fuzzy allow rules, or saved favorites.
- Change model discovery, recommendation ranking, launch guardrails, or tracking modes.
- Add a new persistence field/table for allowed models.

## Decisions

### Use filterable checkboxes plus visible bulk actions

Keep the current checkbox list but add:
- a text input that filters discovered model labels client-side
- `Check visible` to check only currently visible model checkboxes
- `Uncheck visible` to uncheck only currently visible model checkboxes

Rationale: this preserves exact model IDs, avoids typo-prone text entry, and lets operators select groups like `sonnet`, `gpt-5.5`, or `high` without clicking every matching model.

Alternative considered: textarea allow-list. It is compact, but requires exact typing/paste and is easier to typo.

Alternative considered: provider/model presets. Deferred; presets encode product policy and can accidentally authorize too much.

### Keep backend unchanged unless tests expose a gap

The existing `/settings/workers/{adapter_id}/allowed-models` route already receives checkbox values and validates each model is discovered. The UI should keep submitting `allowed_models` values, so no route or schema change is expected.

### Put the enhancement near discovery, not control-plane settings

This is Worker Adapter policy over Worker/coding harness models. It must not be presented as control-plane model/provider setup.

## Risks / Trade-offs

- Client-side JavaScript disabled → fallback remains the existing checkbox list; bulk/filter controls simply do not help.
- Filter term is too broad → operator may check too many visible models; final checked list remains visible before save.
- Very large lists still render many checkboxes → acceptable for this slice; virtualized lists are overkill until rendering itself is slow.
