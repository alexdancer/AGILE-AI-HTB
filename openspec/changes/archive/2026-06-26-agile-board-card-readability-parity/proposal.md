## Why

AGILE Board task cards currently mix summary and verbose evidence inline, which makes the primary scan view noisy and inconsistent with the compact-first behavior used by session/report pages. Operators already expect session report surfaces to present quick, bounded summaries first and let full details expand on demand.

Bringing the board cards to the same readability pattern reduces cognitive load during triage and preserves all evidence needed for audit and review without changing board workflow semantics.

## What Changes

- Update AGILE Board card rendering to keep each card scan-friendly by default (compact summary + key launch metadata).
- Move verbose payloads (full task text, timeline entries, launch failure diagnostics, stdout/stderr, review summaries, and blocked/manual details) into native expandable detail sections.
- Ensure the card model display uses the launched model as primary when available, while retaining the estimator recommendation as secondary evidence when it differs.
- Keep AGILE Board column structure, actions, routing, and state transitions unchanged.
- Add/adjust portal board tests to validate compact behavior and detail discoverability.

## Capabilities

### New Capabilities
- `board-card-readability`: Board task cards SHALL use compact scan summaries by default and expose full verbose evidence through native expandable sections.

### Modified Capabilities


## Impact

- Templates: `src/agile_ai_htb/templates/board.html` (card metadata/layout and detail disclosure behavior).
- Potentially shared template styling in `src/agile_ai_htb/templates/base.html` only if needed for card readability utility classes.
- Portal route/controller tests in `tests/portal/test_board.py` to cover compact-first card rendering and expansion path stability.
- No new external dependencies or API/schema changes expected.