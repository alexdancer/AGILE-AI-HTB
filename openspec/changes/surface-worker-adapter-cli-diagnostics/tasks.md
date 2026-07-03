## 1. Diagnostic extraction

- [x] 1.1 Add a small native CLI diagnostic helper that accepts adapter id/kind plus sanitized stdout/stderr/evidence and returns a bounded user-facing summary, next action, and optional setup link.
- [x] 1.2 Classify Claude Code auth failures from JSONL stdout or stderr containing `Not logged in` and `/login`.
- [x] 1.3 Classify Codex trusted-directory failures from stderr/stdout containing `Not inside a trusted directory` or `--skip-git-repo-check`.
- [x] 1.4 Add unit tests for classifier matches, fallback generic summaries, redaction, and bounded output.

## 2. Verification evidence and Worker Setup

- [x] 2.1 Attach the diagnostic helper output to failed Worker Adapter verification evidence without changing tracking authority or token-accounting rules.
- [x] 2.2 Update Worker Setup view-model rendering so failed Claude Code verification shows the login-required next action in the primary readiness summary.
- [x] 2.3 Keep raw verification stdout/stderr/command evidence behind existing Advanced/details UI with secrets redacted.
- [x] 2.4 Add Worker Setup tests for Claude Code `Not logged in · Please run /login` evidence appearing in primary setup copy and not requiring raw JSON expansion.

## 3. Board launch failure visibility

- [x] 3.1 Attach the diagnostic helper output to retryable Worker Run/task launch failure metadata for native CLI prerequisite exits.
- [x] 3.2 Update AGILE Board task card rendering to show the retryable diagnostic summary, selected adapter, selected model, and project root context when available.
- [x] 3.3 Link adapter/setup-related retryable launch failures to `/settings/workers` while preserving the inline task-card failure summary and retry launch form.
- [x] 3.4 Add Board tests for Codex trusted-directory failure rendering on an Estimated task card after a failed Worker Run.

## 4. Verification

- [x] 4.1 Run targeted tests for Worker Adapter verification, Worker Setup, Board launch selection, and governed Worker launch failure metadata.
- [x] 4.2 Run `openspec validate surface-worker-adapter-cli-diagnostics --strict`.
- [x] 4.3 Run `uv run pytest` after implementation because the repo requires fresh pytest verification after edits.
- [x] 4.4 Manually or via a small script replay the diagnosed evidence strings and confirm the Portal-facing summaries mention Claude Code `/login` and Codex trusted-directory setup without exposing secrets.
