## Why

Current Task Breakdown creates vertical slices and Acceptance Verification, but its policy is too thin for the product goal: AGILE Board cards should be the smallest useful Worker-launchable tasks that preserve the original contract, avoid speculative work, and carry an executable proof. Operators need the Control Plane to apply the same senior-agent task-slicing judgment used in ponytail/minimalism, tracer-bullet planning, TDD feedback-loop discipline, and AFK/HITL issue slicing before Tasks reach the board.

## What Changes

- Add an explicit Harness-owned Task Slicing Policy for the Task Breakdown Agent.
- Strengthen Task Breakdown Agent instructions so candidate Tasks are judged by necessity, vertical-slice value, smallest honest scope, proof quality, dependency clarity, and AFK/HITL execution mode.
- Expand Proposed Task Breakdown candidate structure with policy evidence such as objective, proof/verification, why the slice exists, why it is not smaller/larger, execution mode, dependencies, and likely repo entry points when known.
- Preserve the existing Control Plane / Worker split: the Control Plane produces reviewed board Tasks; Worker Adapters still perform deep execution-time repo inspection.
- Preserve existing Acceptance Verification behavior while making it part of the same policy: final verification remains an ordinary estimated AGILE Board Task, not a whole-task rerun.
- Do not add RAG, embeddings, whole-repo semantic indexing, automatic repair-task creation, hard dependency blocking, or literal Hermes skill loading.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-breakdown-review`: strengthen requirements for Task Breakdown Agent policy, candidate quality evidence, AFK/HITL classification, dependency/proof fields, and rejection of non-task/speculative/horizontal slices.

## Impact

- Affected code:
  - `src/agile_ai_htb/task_breakdown.py` for schema validation and Task Breakdown Agent prompt composition.
  - A new focused policy module such as `src/agile_ai_htb/task_slicing_policy.py` to keep the slicing doctrine reusable and testable.
  - `src/agile_ai_htb/routes/tasks.py` for accepted candidate parsing, metadata persistence, and Worker task-description shaping.
  - Existing Task Breakdown Review templates if the new candidate evidence needs display/edit support.
- Affected tests:
  - Task breakdown validation and golden decomposition fixtures.
  - API/portal tests for accepted candidate persistence and prompt shaping.
  - Launch prompt tests proving implementation slices remain compact while Acceptance Verification keeps enough original contract.
- No dependency, Worker Adapter, tracking-mode, budget-accounting, or provider-client changes expected.
