## 1. Compact Board Card UI

- [x] 1.1 Add minimal shared CSS utilities for compact task summaries, wrapped metadata, and native details spacing in `src/agile_ai_htb/templates/base.html`.
- [x] 1.2 Update `src/agile_ai_htb/templates/board.html` so each task card shows a compact description, key estimate/model line, and the status-specific primary action by default.
- [x] 1.3 Move verbose task ID, full description, Worker timeline, launch stdout/stderr, Agent Review findings, and other noisy diagnostics into native `<details>` sections without changing existing form actions.

## 2. Model Display Accuracy

- [x] 2.1 Update board model display to use `task.metadata.launch_model` as the primary model when present, otherwise `task.recommended_model`.
- [x] 2.2 Show the recommended estimate model as secondary evidence only when it differs from the launched model.

## 3. Verification

- [x] 3.1 Update portal board tests to assert long card content is available behind details while primary actions remain visible.
- [x] 3.2 Add or update a portal test proving an overridden launch model is displayed as primary while the original recommended model remains secondary.
- [x] 3.3 Run targeted portal tests for board rendering.
- [x] 3.4 Run `pytest`.
