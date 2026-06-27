## Context

AGILE Board cards currently render a fixed card surface with many verbose task and execution fields directly visible. Operators now get compact session list/report readability that keeps summaries short and moves raw evidence behind native disclosure blocks. This change aligns board cards with that same policy while preserving the existing board workflow and layout semantics.

The update is scoped to board presentation and related tests only; runtime behavior for task lifecycle, persistence, and worker execution remains unchanged.

## Goals / Non-Goals

**Goals:**
- Keep AGILE Board columns, actions, and state transitions unchanged.
- Make board cards scan-friendly by default via compact metadata + task summary.
- Move long/noisy fields (full task text, timeline entries, stdout/stderr, launch diagnostics, review text, blocked/manual metadata) into expandable `<details>` sections.
- Preserve and clarify model provenance in card headers: show launched model first when available and estimator recommendation second only when different.
- Extend board tests so readable-card behavior and expansion paths are validated.

**Non-Goals:**
- Changing board routing, launch logic, or task lifecycle states.
- Introducing new dependencies or replacing server-rendered templates with a SPA.
- Reworking project workspace/navigation architecture.

## Decisions

### 1) Scope to template-based readability refactor first
AGILE Board card detail parity can be achieved in `board.html` plus CSS utilities in `base.html` with no controller or schema changes.

**Alternative considered:** Add a structured JSON payload API and client-side renderer. **Rejected** because it increases complexity, risks regression in existing action buttons/forms, and is unnecessary for compactness goals.

### 2) Preserve existing metadata flow, reorder model display only in board detail
Use existing payload fields already present in the board card context (`task.recommended_model`, `task.metadata.launch_model`, run metadata) and alter only the render precedence in the template: launched/observed model is primary when available, with estimator recommendation shown as secondary evidence.

**Alternative considered:** Add a separate computed payload field in `portal.py` for model precedence. **Deferred** for now to keep this as a first-slice template-only behavior change and lower risk.

### 3) Use native `<details>` blocks for noisy artifacts
Keep a default compact card summary visible, then nest verbose artifacts under labeled `<details>` regions (task detail, launch artifacts, timelines/logs, review + blocked metadata) with bounded `<pre>` wrappers for log-heavy fields.

**Alternative considered:** Replace detail blocks with custom accordion JS. **Rejected** because existing HTML disclosure is accessible enough, keeps the change low-risk, and matches the session/report pattern.

### 4) Minimal shared styling footprint
Add/adjust only small reusable utility classes in `base.html` for clamping and overflow wrapping used by both board cards and existing session/report views, avoiding duplication and CSS drift.

**Alternative considered:** Inline per-block styles inside `board.html`. **Rejected** to keep style consistency and avoid repeated verbose classes across cards.

## Risks / Trade-offs

- **[Risk] Hidden evidence discoverability**: Operators may not notice nested evidence sections.
  - **Mitigation**: Keep section labels explicit (`Details`, `Launch`, `Timeline`, `Logs`, `Review`, `Blocked`) and ensure each card still exposes the most commonly used fields in the compact summary.

- **[Risk] Layout variance across large payloads**: Expanded detail blocks can create tall cards.
  - **Mitigation**: Use bounded `max-height` wrappers with overflow scrolling for raw payload fields (stderr/stdout/task text/timeline), mirroring existing session report behavior.

- **[Risk] Existing visual assumptions in tests**: Snapshot/content checks may couple to exact card text.
  - **Mitigation**: Implement tests to assert functional behavior and presence of key fields rather than exact full raw content placement.

## Migration Plan

- No DB/schema migration is required.
- Implementation is limited to template + CSS + test updates.
- Rollout steps:
  1. Merge proposal artifacts after `/opsx-apply`.
  2. Update `board.html` and `base.html`.
  3. Update `tests/portal/test_board.py` assertions.
  4. Run focused board session tests and targeted suite.

## Open Questions

- None; behavior is bounded and intentionally aligned with existing session/report readability pattern.