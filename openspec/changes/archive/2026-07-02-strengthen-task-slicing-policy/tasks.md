## 1. Policy and schema

- [x] 1.1 Add `src/agile_ai_htb/task_slicing_policy.py` with the Task Slicing Policy text, allowed execution modes (`AFK`, `HITL`), and reusable prompt fragments for necessity, vertical-slice, YAGNI/minimalism, proof, dependency, and repo-context-hint rules.
- [x] 1.2 Extend Task Breakdown candidate validation in `src/agile_ai_htb/task_breakdown.py` to accept structured quality evidence: objective, proof/verification path, why-this-task-exists, why-not-smaller, why-not-larger, dependencies, likely entry points, execution mode, and HITL reason.
- [x] 1.3 Keep candidate `kind` limited to `implementation` and `acceptance_verification`; validate `execution_mode` separately and default legacy records safely for existing breakdown data.
- [x] 1.4 Compose the Task Breakdown Agent system prompt from the existing agent identity, the new Task Slicing Policy, and the required output schema.

## 2. Breakdown acceptance and prompt shaping

- [x] 2.1 Update accepted-candidate parsing in `src/agile_ai_htb/routes/tasks.py` to preserve policy evidence from the review form or original candidate payload.
- [x] 2.2 Persist policy evidence into created Task metadata when accepted candidates become Estimated AGILE Board Tasks.
- [x] 2.3 Update `_breakdown_candidate_description()` so implementation Tasks include objective, compact global contract, scope boundary, acceptance criteria, constraints, dependencies, and proof while still omitting unrelated raw source prose.
- [x] 2.4 Preserve Acceptance Verification behavior so verification Tasks keep enough original source contract and remain framed as proof, not reimplementation.

## 3. Review UI evidence

- [x] 3.1 Update the Task Breakdown Review page to show execution mode, proof, and key slicing evidence for each candidate without turning the page into a full planning editor.
- [x] 3.2 Allow practical editing of execution mode, proof/verification, and HITL reason before accepting candidates.
- [x] 3.3 Render detailed quality evidence in compact/native details blocks where needed so the review remains readable.

## 4. Tests and fixtures

- [x] 4.1 Add validation tests proving candidates require policy evidence, invalid execution modes fail, and legacy/minimal candidate records normalize safely where supported.
- [x] 4.2 Add deterministic fake-LLM Task Breakdown tests for unnecessary/speculative items, constraints, verification notes, and horizontal layer bullets being rejected or classified as non-task evidence.
- [x] 4.3 Add decomposition fixture coverage proving candidates include AFK/HITL classification, proof, why-not-smaller/larger rationales, dependencies, and likely repo entry-point hints when repo context is supplied.
- [x] 4.4 Add acceptance-flow tests proving created Task metadata preserves policy evidence and implementation descriptions include proof/boundaries without copying unrelated raw source prose.
- [x] 4.5 Add launch prompt regression coverage proving Repo Context Brief still wraps the shaped Task description and Acceptance Verification still receives the original source contract.

## 5. Documentation and verification

- [x] 5.1 Update `CONTEXT.md` glossary entries for Task Breakdown Agent and Proposed Task Breakdown to describe Task Slicing Policy, execution mode, and candidate quality evidence.
- [x] 5.2 Run focused tests for task breakdown, task estimation/acceptance flow, and launch prompt injection.
- [x] 5.3 Run `openspec validate strengthen-task-slicing-policy --strict`.
- [x] 5.4 Run `uv run pytest` after implementation edits and resolve any failures caused by this change.
