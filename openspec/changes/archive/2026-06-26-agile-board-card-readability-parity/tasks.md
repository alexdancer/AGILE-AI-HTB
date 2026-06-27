## 1. Template and Rendering Changes

- [x] 1.1 Update `src/agile_ai_htb/templates/board.html` card summary to keep default display compact and avoid long raw text in the card header.
- [x] 1.2 Move full task body and verbose fields into native `<details>` sections (e.g., task body, launch evidence, worker timeline, stdout/stderr, review state).
- [x] 1.3 Implement model precedence in board rendering: show launched model as primary when present, then estimator recommendation as labeled secondary evidence if different.
- [x] 1.4 Ensure verbose sections use bounded containers (`max-height` + `overflow`) so expansion stays readable and scrollable.

## 2. Shared Styles

- [x] 2.1 Add/update minimal shared utility classes in `src/agile_ai_htb/templates/base.html` for compact text and evidence block wrapping used by board cards.
- [x] 2.2 Confirm existing session/report readability styles are not regressed by any class reuse.

## 3. Board Test Coverage

- [x] 3.1 Update `tests/portal/test_board.py` assertions to verify default board cards are compact and verbose fields are still present in expandable sections.
- [x] 3.2 Add/adjust tests for model provenance display when launch model differs from recommendation.
- [x] 3.3 Add/adjust tests to verify long artifacts are bounded and wrapped in `<pre>` style output where expected.

## 4. Validation

- [x] 4.1 Run `uv run pytest tests/portal/test_board.py` and capture output.
- [x] 4.2 Run focused board/session regression command after implementation: `uv run pytest tests/portal/test_board.py tests/portal/test_sessions.py`.
- [x] 4.3 Validate that template changes satisfy readability expectations with a reviewer walkthrough of key board card states (idle, running, blocked, reviewed).
