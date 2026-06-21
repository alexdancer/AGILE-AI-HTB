## Context

The current board launch path calls `launch_task()` from the HTTP request handler and then runs the selected Worker Adapter command with the subprocess runner before the response returns. This makes long-running coding-agent sessions behave like a blocking form submit: the task is marked `Running` in SQLite, but the browser stays loading until the adapter command exits or times out.

The product lifecycle needs a clearer separation:

```text
Control Plane / Board
  estimates task
  launches Worker Run
  stays usable

Worker Run
  executes OpenCode/Codex/Claude/demo-worker command
  records evidence
  updates task status when complete
```

There are currently no active OpenSpec changes, so this change introduces the next lifecycle contract directly.

## Goals / Non-Goals

**Goals:**

- Make Launch an asynchronous operation that starts a background Worker Run and returns immediately.
- Remove the redundant `Ready` lifecycle column; `Estimated` is the launchable pre-run state.
- Persist Worker Run state/evidence in SQLite so board and session pages can recover status after navigation.
- Move successful Worker Runs from `Running` to `Review` with stdout/stderr, session/token evidence, and git diff/porcelain evidence where available.
- Move retryable Worker Run failures back to `Estimated` with inline error evidence, not `Blocked`.
- Keep `Blocked` reserved for workflow/manual/safety blockers.
- Use an in-process background runner for the first slice to avoid Redis/Celery or hosted queue infrastructure.

**Non-Goals:**

- No hosted workspace or remote execution queue in this slice.
- No streaming terminal UI or full live transcript viewer in this slice.
- No replacement of the Worker Adapter contract; OpenCode/Codex/Claude/demo-worker adapters still produce command plans.
- No automatic PR/merge flow change beyond surfacing Review evidence.

## Decisions

### Decision: Launch creates a persisted Worker Run and returns immediately

`POST /tasks/{task_id}/launch` should validate launch guardrails, create/update a session, persist a Worker Run record, mark the task `Running`, start background execution, and return a redirect/JSON response without waiting for the adapter subprocess to exit.

Alternatives considered:

- Keep synchronous launch and increase timeouts. Rejected because it keeps the board unusable during long coding-agent runs.
- Poll a synchronous request from the browser. Rejected because it still ties execution to the request lifecycle.

### Decision: Use in-process background execution for the first slice

The first implementation should use an in-process background runner attached to the local FastAPI app process, backed by SQLite Worker Run records for observable state. This preserves local/demo simplicity while creating the seam for a later durable runner or queue.

Alternatives considered:

- Redis/Celery/RQ now. Rejected as too much infrastructure for the immediate demo and local-runner slice.
- Hermes process tracking as the product execution engine. Rejected because product behavior should not depend on the agent running this coding session.
- Hosted queue/workspace now. Rejected because Control Plane vs Execution Plane scale-out can come after the lifecycle contract is truthful.

### Decision: Worker Adapter means local coding-agent CLI integration

A Worker Adapter adapts an installed coding-agent CLI such as OpenCode, Claude Code, Codex, Hermes, or a custom command. It is responsible for detecting the CLI, discovering supported models through CLI-native commands where possible, building a launch command, running it in the configured workdir, and recording sanitized runtime evidence. Proxy governance is a tracking mode, not the definition of the adapter.

Launchability depends on the verified tracking mode:

- `proxy_governed` launches route Worker model traffic through the Harness Proxy and are budget-authoritative when token rows are recorded.
- `native_usage` launches use trustworthy machine-readable CLI-emitted usage evidence and are budget-authoritative when that evidence is parsed, bound to the launched Worker Run, and recorded. Trustworthy evidence includes selected model, prompt/input tokens, completion/output tokens, total tokens, exit status, and command/session identity or equivalent run-binding evidence. Human-readable logs, approximate usage, missing model identity, or unbound usage evidence is not authoritative.
- `observed_only` launches may be useful for diagnostics but are not launchable for governed Tasks.

Only `proxy_governed` provides runtime request governance because Worker model calls pass through the Harness Proxy. `native_usage` provides budget-authoritative accounting without request-time enforcement; the Harness can preflight budget, reconcile after the run, review evidence, and raise alarms after usage is known. `observed_only` provides process/log observation only and is never launchable from the normal AGILE Board.

Budget override approval is allowed for both `proxy_governed` and `native_usage` launchable modes when the task estimate exceeds remaining daily Worker budget. `proxy_governed` keeps runtime request guardrails available after the override. `native_usage` requires explicit acknowledgement that the Harness cannot request-throttle native CLI model calls mid-run and that post-run reconciliation may show an overrun. `observed_only` has no AGILE Board budget override path because it is not task-launchable.

Observed-only runs belong in a separate Worker Setup diagnostic/test flow, not task dispatch. A diagnostic run can prove command start, stdout/stderr capture, exit code or timeout handling, detected model when available, and a not-budget-authoritative warning. It must not change task state, show Launch-ready, or claim governed execution.

Portal labels should be explicit about governance strength: `proxy_governed` displays as **Governed via Harness Proxy**, `native_usage` displays as **Tracked via Native Usage**, and `observed_only` displays as **Observed Only**. UI copy should show launch readiness separately from tracking strength and should not use a generic "Governed" badge for all launchable adapters.

### Decision: Estimated replaces Ready

`Estimated` should represent a task that has enough estimation/model information to be launchable when Worker guardrails pass. The `Ready` column adds ambiguity without a distinct lifecycle responsibility and should be removed from canonical board columns and status validation.

### Decision: Success transitions to Review with evidence

A successful Worker Run should move the task `Running -> Review`, not leave it in `Running`. Review is where the operator inspects stdout/stderr, session/token evidence, diff/porcelain evidence, and any verification summary before marking Done.

### Decision: Retryable run failure returns to Estimated

If a Worker Run starts but later times out, exits nonzero, or lacks required usage evidence, the task should return to `Estimated` with retryable error metadata. This keeps the task relaunchable and avoids polluting `Blocked` with operational failures.

Hard safety failures remain blocking. Examples: read-only Worker modified the repo, write-capable verification failed in a way that requires manual intervention, or a dependency/manual blocker is explicitly present.

## Risks / Trade-offs

- **In-process runner dies with the web process** → Persist Worker Run records with `running`/`started_at` metadata so stale runs can be surfaced as interrupted/retryable instead of disappearing.
- **SQLite concurrency under background writes** → Keep updates small and serialized through existing DB helpers; avoid long write transactions.
- **Duplicate launches from repeated clicks** → Add a Running/active-run guard so a task cannot have multiple active Worker Runs unless explicitly retried after failure.
- **Adapter output can be large** → Store sanitized/truncated stdout/stderr for board display and preserve larger artifacts only if the project already has an artifact path convention.
- **Removing Ready may affect old data** → Treat existing `Ready` tasks as `Estimated` during migration or first display update, then stop creating new `Ready` tasks.
