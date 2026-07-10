## 1. Bounded Backend Board Contracts

- [x] 1.1 Refactor the React project-board state handoff to project `board_page_context()` into the specified fixed top-level, canonical-status maps, adapter, card, named controls, and fully shaped detail allowlists instead of returning raw context or metadata.
- [x] 1.2 Sanitize and bound React card evidence using the specified task-body, launch/log/review/blocked, timeline, and Agent Review limits plus post-redaction truncation indicators; exclude secrets, session credentials, adapter config, verification payloads, and raw token-ledger records.
- [x] 1.3 Preserve backend-authoritative project scope, archived/unknown project handling, canonical columns, allowed Worker model constraints, model provenance, Worker-only actual token values, queue policy, and review-action availability in the projection.

## 2. Negotiated Existing Board Actions

- [x] 2.1 Add explicit `Accept: application/json` negotiation with fixed `ok`, `error`, `setup_href`, and `next_href` outcomes to existing task launch, refresh, review, project archive/dismiss, archive-all-Done, run-next, and queue action paths without changing Jinja form redirects.
- [x] 2.2 Add a JSON-capable project-scoped intake outcome for React short-text and Markdown/file submission that sends every Markdown paste/upload through Task Breakdown Review, returns its authoritative URL, and preserves file-over-text precedence.
- [x] 2.3 Return sanitized structured action failures and relevant setup links for React callers while preserving existing launch guardrail, budget/native-usage acknowledgement, project-binding, queue, review, and archive validation.

## 3. React Board Workflow

- [x] 3.1 Replace the read-only `Board.jsx` view with a bounded-state board controller that refetches authoritative state after mutations and navigates to explicit non-migrated workflow URLs only when required.
- [x] 3.2 Add React task intake with Markdown upload, local filtering, board summary/history, run-next, queue start/stop, and Auto Agent Review controls using existing project-scoped action paths.
- [x] 3.3 Add compact status-card components for Estimated, Running, Review, Done, and Blocked states with adapter/model selection, budget/native acknowledgement, launch/refresh/review/disposition/archive/dismiss controls, and actionable guardrail feedback.
- [x] 3.4 Add native bounded details for task text, normalized Worker token components, launch data, timeline, logs, Agent Review, and blocked evidence; show launched Worker model before routed recommendation when different.
- [x] 3.5 Reuse shared Portal CSS tokens/primitives for board controls, cards, details, filters, notices, and responsive board layout without adding state-management, UI, or drag/drop dependencies.
- [x] 3.6 Reuse existing active-run/queue status polling only while live refresh is required and retain manual Running-card refresh.

## 4. Regression Coverage

- [x] 4.1 Add backend tests for portal auth, project scope, archived/missing project errors, exact nested board-projection allowlists (including controls, every detail object, review evidence, and finding/timeline fields), null/empty defaults, redaction/bounds/truncation flags, token/model semantics, and newest-six timeline behavior.
- [x] 4.2 Add backend tests proving explicit JSON negotiation and minimum outcome shape preserve Jinja redirects and existing validation for intake, every-Markdown breakdown handoff/file precedence, launch guardrails, native budget acknowledgement, queue controls, review disposition, archive/dismiss, and project binding.
- [x] 4.3 Expand frontend SSR/source contracts for board loading/error/empty states, local filtering, intake, all status actions, adapter-constrained models, queue controls, compact-details evidence, model provenance, and full-page fallback links.
- [x] 4.4 Run targeted React-board tests, `npm --prefix frontend run check`, `uv run pytest tests/portal/test_react_shell.py -q`, `uv run pytest -q`, `openspec validate react-board-functional-parity --strict`, and `git diff --check`.
