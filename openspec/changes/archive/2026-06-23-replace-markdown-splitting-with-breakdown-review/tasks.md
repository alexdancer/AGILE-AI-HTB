## 1. Data Model and Contracts

- [x] 1.1 Add durable Proposed Task Breakdown storage for source metadata, status, agent output, candidates, constraints, rejected/non-task items, failure details, model identity, and linked token/session evidence.
- [x] 1.2 Define validation schemas for Task Breakdown Agent structured output, including `single_task` and `proposed_task_breakdown` decisions.
- [x] 1.3 Add settings/config support for a separate Task Breakdown Model with documented fallback behavior.

## 2. Task Breakdown Agent Flow

- [x] 2.1 Replace direct deterministic Markdown-to-Task creation in intake with Task Breakdown Agent invocation for Markdown upload and Markdown paste.
- [x] 2.2 Route clearly oversized plain-text intake through the Task Breakdown Agent while preserving direct estimation for short plain-text tasks.
- [x] 2.3 Record Task Breakdown Agent usage as `task_breakdown` Orchestration Tokens linked to the Proposed Task Breakdown.
- [x] 2.4 Preserve deterministic Markdown parsing only as optional structure hints for prompts, not as product fallback or direct Task creation.
- [x] 2.5 Implement explicit failure/manual recovery state for invalid output, unavailable model, budget failure, or provider error.

## 3. Breakdown Review UX

- [x] 3.1 Add a separate breakdown review page for Proposed Task Breakdown records.
- [x] 3.2 Show candidate vertical slices, constraints, verification criteria, non-goals/rejected items, reasons, confidence, and recommended sequence.
- [x] 3.3 Support practical editing: accept/reject candidates, edit titles/prompts, edit constraints, and edit acceptance criteria.
- [x] 3.4 Ensure single-task Markdown decisions still go through the review page before estimation.
- [x] 3.5 Submit accepted candidates directly into Task Estimation and redirect back to the AGILE Board with Estimated cards.

## 4. Replace Old Deterministic Splitting Behavior

- [x] 4.1 Remove or bypass product behavior that creates one Estimated Task per raw Markdown checklist/bullet item.
- [x] 4.2 Replace tests that assert checklist bullets directly create multiple Tasks with tests asserting review creation and zero Tasks before acceptance.
- [x] 4.3 Ensure accepted candidate Tasks inherit relevant constraints and acceptance criteria in metadata or task text before estimation.
- [x] 4.4 Search docs/tests/demo runbooks for stale deterministic-splitting language and update source-of-truth wording.

## 5. Evals and Verification

- [x] 5.1 Add golden decomposition fixtures covering implementation bullets, constraints, verification criteria, non-goals, and rejected-as-task reasons.
- [x] 5.2 Add regression coverage for “Do not add network dependencies.” as a constraint, not a standalone Task.
- [x] 5.3 Add product-flow tests for Markdown upload/paste → durable review → accept candidates → Estimated board cards.
- [x] 5.4 Add failure-path tests for invalid model output/manual recovery with no silent deterministic fallback.
- [x] 5.5 Run targeted task intake, portal, and decomposition eval tests.
- [x] 5.6 Run `pytest` for the relevant suite before marking implementation tasks complete.
