## Context

The current AGILE Board already has the core governed lifecycle: Estimated tasks can launch a Worker Adapter, launches start background Worker Runs, Running tasks can complete into Review, and operators can use Agent Review, Mark Done, or Block from Review. The remaining friction is operational: operators must refresh status manually, launch each eligible task manually, and manually request Agent Review after each successful Worker Run.

This change automates those repetitive board operations without crossing into Level 4 autonomy. The harness may launch eligible tasks under an explicit project-scoped queue policy and may prepare review evidence, but it must not decide final task acceptance or create repair loops.

Model responsibilities remain split:

- The control-plane/orchestrator model powers estimation, task breakdown, Agent Review, reports, and automation summaries.
- Worker/coding harness models are selected through Worker Adapters such as OpenCode, Claude Code, Codex, or Hermes.
- Worker Adapter identity remains separate from tracking mode (`proxy_governed`, `native_usage`, `observed_only`). Automation can only launch board-governed adapters that already pass launch guardrails.

## Goals / Non-Goals

**Goals:**

- Keep project boards current while Worker Runs are active.
- Add bounded project-scoped automation controls for `Run next task` and `Run queue`.
- Launch only eligible Estimated tasks for the selected project.
- Run at most one Worker Run at a time by default.
- Continue queue execution past tasks that reach Review, because Review is not a running slot.
- Optionally trigger Agent Review after successful Worker Runs.
- Record automation evidence and stop reasons.
- Preserve human-only Review disposition.

**Non-Goals:**

- No automatic Mark Done.
- No automatic Block based only on Agent Review output.
- No automatic repair task creation.
- No cross-project autopilot.
- No observed-only Worker Adapter launch from the AGILE Board.
- No automatic budget override or native usage acknowledgement.
- No frontend framework, websocket dependency, or full board rewrite in the first slice.

## Decisions

### Decision: Project-scoped automation only

Run automation starts from `/projects/{project_id}/board` and only considers tasks bound to that project. The global `/board` may show live state, but queue actions require an explicit project context.

Alternatives considered:

- Global queue across all projects: rejected because it risks launching against the wrong repository and weakens the project workspace model.
- Most-recent project fallback: rejected because launch target must be explicit and auditable.

### Decision: One active Worker Run at a time

The queue launches one eligible task, waits for that Worker Run to finish or fail, then evaluates whether to launch the next eligible task. Review tasks do not block queue continuation because they are awaiting human disposition, not consuming the running Worker slot.

Alternatives considered:

- Parallel Worker Runs: deferred because budget evidence, dirty-repo safety, and review UX are easier to trust with one-at-a-time execution.
- Stop at every Review: rejected for Level 3 because it collapses queue behavior into repeated `Run next` clicks.

### Decision: Conservative stop conditions

The queue stops when no eligible tasks remain, launch guardrails fail, budget override would be required, native usage acknowledgement would be required, a retryable Worker failure occurs, a hard safety/manual block occurs, the selected project disappears, or the operator stops the queue.

Retryable Worker failure remains an Estimated task with inline evidence. Hard safety/manual blockers may move to Blocked according to existing lifecycle semantics.

### Decision: Auto Agent Review is advisory evidence

When enabled, successful Worker Runs that enter Review automatically request Agent Review using the control-plane/orchestrator model and existing review evidence. Auto Agent Review result metadata is displayed on the Review card, but it never changes task status to Done or Blocked.

Alternatives considered:

- Auto-Mark Done on clean Agent Review: rejected as Level 4 autonomy.
- Auto-Block on Agent Review findings: rejected because Review Disposition remains an operator decision.

### Decision: Polling first, not websockets

The board can use light polling or timed refresh to update Running/queue status. This fits the existing server-rendered UI and avoids introducing a realtime subsystem before the product needs it.

Alternatives considered:

- Websocket/live event stream: deferred until there is a stronger need for interactive logs.
- SPA board rewrite: rejected as unnecessary for this slice.

## Risks / Trade-offs

- Queue state can become stale if the server restarts mid-run → Persist queue metadata and recover by marking stale Worker Runs interrupted, then show the queue stopped with evidence.
- Auto Agent Review can fail due to control-plane model configuration → Leave the task in Review and show review failure metadata without changing disposition.
- Operators may misunderstand queue as full autopilot → Copy must say `project only`, `one at a time`, `stops before budget/manual/safety decisions`, and `human still marks Done`.
- Native usage adapters cannot be throttled mid-run → Queue must never auto-acknowledge native budget override; it stops and asks for operator action.
- Dirty write-capable repos may stop queues often → This is correct; the Repository Cleanliness Guardrail must remain authoritative.

## Migration Plan

1. Add metadata/schema handling for run automation state without changing existing task status names.
2. Add board live refresh/polling for current Running tasks.
3. Add project-scoped `Run next task` and queue start/stop/status routes.
4. Add optional Auto Agent Review trigger after successful Worker completion.
5. Add board UI copy and evidence display.
6. Keep all existing manual launch/review controls available.

Rollback is straightforward: disable/hide automation controls while retaining existing manual launch, refresh, Agent Review, Mark Done, and Block flows.

## Open Questions

- Should the first implementation persist queue state only in task/project metadata, or introduce a dedicated queue table for clearer history?
- Should queue order be strict task creation order, recommended sequence metadata when present, or a visible operator-selected order? The initial default should be deterministic and simple: existing board order for Estimated tasks.
