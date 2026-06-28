## Context

The Control Plane settings page already separates the harness's own orchestration model from Worker Adapter models and persists Control Plane settings through the operator config. The current UI has provider presets and a provider `<select>`, but the model field is an `<input list="control-plane-model-options">` backed by a `datalist`. That is technically editable and has options in markup, but it is not a dependable dropdown UX and can appear as a plain textbox.

This change is a small portal UX correction on top of the existing live-save behavior. It should not change the source of truth, API key handling, connection testing, Worker Adapter model discovery, or task launch model selection.

## Goals / Non-Goals

**Goals:**

- Make the normal Control Plane model picker an actual dropdown for curated model choices.
- Keep provider/model pairings clear so choosing OpenAI, Anthropic, or OpenAI-compatible does not produce surprising invalid combinations.
- Preserve a custom model path for OpenAI-compatible providers and future model IDs.
- Preserve existing save/hot-swap/stale-test semantics and secret redaction guarantees.
- Update portal tests to assert the real dropdown contract.

**Non-Goals:**

- No provider catalog/model discovery API.
- No Worker Adapter model inventory or allowed-model change.
- No database migration or new dependency.
- No change to estimation, task breakdown, or launch routing beyond the saved Control Plane model value already used today.
- No broad portal frontend rewrite.

## Decisions

1. Use a real `<select>` for curated Control Plane models.

   Rationale: the bug is that the current model field is perceived as a textbox rather than a dropdown. A native `<select>` gives the expected browser affordance, keyboard behavior, and testable markup.

   Alternative considered: keep `datalist` and add CSS/help text. Rejected because `datalist` remains browser-specific and still behaves like free text.

2. Preserve custom model entry as an explicit custom path, not as the normal control.

   Rationale: OpenAI-compatible endpoints and future IDs still need free-text support, but the default operator path should be curated and simple. The implementation can use a custom option plus a text input shown in advanced/custom mode, or an equivalent accessible pattern, as long as the submitted `control_plane_model` remains the selected/custom model value.

   Alternative considered: remove custom model entry entirely. Rejected because OpenAI-compatible setup explicitly requires a custom model/base URL path.

3. Keep Control Plane model choices separate from Worker model choices.

   Rationale: this page configures the harness's own estimator/planning/reporting model, not OpenCode/Claude Code/Codex launch models. Pulling Worker Adapter discovered models into this dropdown would collapse model layers and create invalid credentials/launch assumptions.

   Alternative considered: reuse Worker Adapter discovered models. Rejected because Worker Adapter models belong to the execution layer and may use native CLI auth or tracking modes unrelated to Control Plane provider credentials.

4. Keep the curated list tiny and local to the existing settings page unless a stronger source of truth already exists.

   Rationale: this is a UX bug fix, not a model catalog project. The current page already names the intended curated values. Implementation may keep these as template context or a small helper, but should avoid introducing external discovery or broad configuration machinery.

## Risks / Trade-offs

- Existing custom saved model may not be in the curated list → The UI must preserve it through a custom option/path so opening and saving the page does not silently replace it.
- Provider/model mismatch remains possible if the operator manually switches provider after selecting a model → Preset buttons and/or minimal client-side filtering should keep common choices coherent, while server-side validation remains focused on required field shape and OpenAI-compatible base URL.
- Hidden custom text input could be missed by tests → Add portal tests for curated dropdown markup and preservation of custom/current values.
- More JavaScript could make the simple server-rendered page brittle → Prefer native controls and small vanilla JS only for toggling preset/custom visibility.
