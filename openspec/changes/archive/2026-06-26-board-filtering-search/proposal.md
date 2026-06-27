## Why

The AGILE Board has no search or filter capability. With 10+ tasks across 5 columns, operators scroll through cards hunting for a specific task name, model, or status. A single text input that filters cards in-place is the simplest fix — no new routes, no DB changes, just client-side filtering.

## What Changes

- Add a text `<input>` above the board columns in `board.html`
- On keystroke, filter all `.task` cards: show cards whose description or metadata text contains the query (case-insensitive)
- Show a match count indicator (e.g., "3 of 12 tasks visible")
- Empty query restores full visibility
- Columns with zero visible cards show an "empty" state
- Zero dependencies — vanilla JS inline in the template

## Capabilities

### New Capabilities

- `board-filtering`: The AGILE Board supports client-side text filtering across all columns, with a match count indicator.

### Modified Capabilities

None. Additive only.

## Impact

- `src/agile_ai_htb/templates/board.html`: Filter input + ~20 lines of inline JS
- `tests/portal/test_board.py`: 2 new tests (filter hides non-matching cards, filter shows match count)
