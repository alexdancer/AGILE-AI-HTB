## 1. Add checkpoints section to session report template

- [x] 1.1 Add checkpoints section to `templates/session_report.html` (render each checkpoint with name, pass/fail pill, details)
- [x] 1.2 Hide section when `artifact.checkpoint_results` is empty or absent

## 2. Add tests

- [x] 2.1 Add portal test: session report renders checkpoint results when present
- [x] 2.2 Add portal test: session report omits checkpoints section when empty

## 3. Verify

- [x] 3.1 Run full pytest suite, fix any failures
