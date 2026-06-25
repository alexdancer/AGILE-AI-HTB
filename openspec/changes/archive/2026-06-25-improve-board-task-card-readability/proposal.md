## Why

AGILE Board task cards are hard to scan because long descriptions, diagnostics, timelines, review evidence, and launch controls all render expanded by default. The board also stores the operator-selected launch model, but the card still emphasizes the estimator's recommended model, which can mislead operators after a model override.

## What Changes

- Make task cards compact by default: show a short task summary, key token/model status, and the primary action for the card's current column.
- Move verbose evidence and diagnostics into native expandable details on the existing card.
- Show the actual launched Worker model as the primary model value when it differs from the recommended estimate model, while preserving the recommendation as secondary evidence.
- Keep the existing board columns, forms, adapter/model selection behavior, and Worker Run lifecycle.
- Do not add new JavaScript, dependencies, drag/drop behavior, or a board rewrite.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `board-launch-selection`: Compact board card rendering and actual launched model display change board launch/readability behavior.

## Impact

- Affected UI templates: `src/agile_ai_htb/templates/board.html` and shared styles in `src/agile_ai_htb/templates/base.html`.
- Affected tests: portal/board rendering tests covering compact cards, details disclosure content, and launch model override display.
- No database schema changes, new dependencies, or API changes expected.
