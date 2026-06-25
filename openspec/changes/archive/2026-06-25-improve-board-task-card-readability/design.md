## Context

The current board renders each task card with the full description, IDs, model metadata, launch controls, Worker timeline, launch errors, stdout, review prompt, Agent Review, findings, and disposition controls inline. That makes normal board scanning difficult once tasks contain long descriptions or run evidence.

The launch flow already records the operator-selected Worker model in existing places: session model, Worker Run model, and task metadata `launch_model`. The board should use that existing launch evidence instead of treating `recommended_model` as the only visible model after launch.

## Goals / Non-Goals

**Goals:**

- Keep the board readable by making each task card compact by default.
- Keep the primary column action visible without forcing operators to open details.
- Preserve verbose evidence on the card through native disclosure UI.
- Show the actual launched Worker model as primary when it exists and differs from the estimate recommendation.
- Reuse existing task metadata and Worker Run data.

**Non-Goals:**

- No board rewrite, drag/drop, SPA, websocket updates, or new card component framework.
- No schema migration or new persisted model field.
- No change to estimator routing, adapter/model dropdown behavior, launch guardrails, or Worker Run lifecycle.
- No new JavaScript beyond the existing adapter/model dropdown behavior.

## Decisions

- Use native `<details>` / `<summary>` for verbose task evidence.
  - Rationale: built into HTML, accessible enough for this slice, no dependency or custom state code.
  - Alternative rejected: custom accordion JavaScript because it adds code for behavior the browser already has.

- Add small CSS utilities for clamped/wrapping card text in `base.html`.
  - Rationale: shared template styles already live there, and the board only needs simple presentation helpers.
  - Alternative rejected: pre-truncating descriptions server-side because the full value should remain available in the DOM/details without extra view-model code.

- Compute display model in the board template from existing values.
  - Primary model: `task.metadata.launch_model` when present; otherwise `task.recommended_model`.
  - Secondary model: show `Recommended: ...` only when `launch_model` exists and differs from `recommended_model`.
  - Rationale: preserves recommendation provenance while making launched reality obvious.
  - Alternative rejected: overwriting `recommended_model` on launch because it loses estimator evidence.

- Keep primary controls inline by status.
  - Estimated: adapter/model selectors and Launch task remain visible.
  - Running: active run and refresh remain visible.
  - Review: review disposition controls remain visible.
  - Verbose evidence moves under details.

## Risks / Trade-offs

- CSS line clamping can hide context operators wanted at a glance → full description remains available in details.
- Moving evidence into details can make debugging one click deeper → errors and primary status remain visible; only noisy stdout/timeline/findings move.
- Template-only model display depends on `metadata.launch_model` being populated for launched tasks → existing launch flow already writes it; tests should cover override display.
