## Context

Local demo testing showed a launch timeout from the Worker adapter path:

```text
launch_returncode = 124
launch_stderr = "Command timed out after 60 seconds."
```

The current launch path then updates the task to `Blocked`, stores `launch_blocked_reason`, and future launch attempts fail guardrails because only `Estimated` or `Ready` tasks can launch. That makes a recoverable operational failure look like a workflow dependency block.

Current relevant flow:

```text
Board form
  → POST /tasks/{id}/launch
  → launch_task()
  → subprocess_runner()
  → nonzero return code / missing usage evidence
  → task.status = Blocked
```

The board also only exposes a one-line task description field for estimation. There is no markdown textarea or `.md` upload path, even though the demo needs to analyze repo-oriented task files and decompose longer/bullet-point work.

The alarm path exists through proxy/session artifacts, but the demo needs behavior-specific evals that prove budget-zone and cap-boundary alarms work and remain visible, not just scattered unit assertions.

## Goals / Non-Goals

**Goals:**

- Separate workflow blocking from recoverable launch failures.
- Preserve relaunchability for `Estimated`/`Ready` tasks when a Worker launch fails operationally.
- Keep sanitized launch evidence on the task/session for debugging and UI display.
- Make local/demo Worker launch timeouts compatible with real model-call latency.
- Add markdown task intake through board/API form handling.
- Add behavioral evals for markdown task decomposition and budget alarm behavior.
- Preserve the control-plane versus Worker model separation: estimator/control-plane calls are not the same as Worker execution calls.

**Non-Goals:**

- Replacing the existing board with a new UI framework.
- Redesigning the entire task lifecycle or Kanban model.
- Adding real dependency graph management beyond preserving the meaning of `Blocked` for workflow/dependency blockers.
- Changing provider authentication semantics for OpenCode, Codex, Claude Code, or other Worker harnesses.
- Making alarms a full external notification system; this change focuses on detection, persistence, and visibility.

## Decisions

### 1. Treat operational launch failures as recoverable launch errors

For nonzero Worker command results, subprocess timeouts, and missing required usage evidence after a Worker run, `launch_task()` should restore/preserve the pre-launch task lifecycle status when that status was launchable (`Estimated` or `Ready`). The task should store sanitized evidence under metadata such as:

- `launch_error` for the current user-visible retryable launch error
- `last_launch_failure` for structured sanitized failure evidence
- `launch_returncode`
- `launch_stderr`
- existing sanitized `launch_command_plan`

The UI should show this as an inline error on the same task card while keeping the launch button visible.

Alternative considered: keep setting status to `Blocked` and add an "unblock" button. Rejected because it preserves the wrong semantic model: `Blocked` should mean a workflow or dependency block, not an adapter timeout.

### 2. Keep hard guardrail violations distinct from recoverable runtime failures

Some failures should still prevent launch and may still produce `Blocked` or explicit blocked metadata:

- task is not in a launchable lifecycle state before launch
- task requires manual estimate before launch
- adapter is unverified or unavailable
- selected Worker model is unsupported by discovered Worker models
- read-only Worker modifies the connected project
- write-capable verification fails and preserves an uncommitted diff for review

These are different from a launch process timing out or a model-backed demo Worker returning nonzero. The implementation should use separate metadata names and user-facing copy for:

```text
workflow block / guardrail block ≠ operational launch failure
```

Alternative considered: make every `TaskLaunchBlocked` non-mutating. Rejected because some guardrails intentionally enforce task lifecycle state or safety constraints.

### 3. Make Worker subprocess timeout configurable by command plan or adapter config

The current `subprocess_runner()` uses one module-level 60-second timeout. The demo Worker can make several real model calls through the Harness Proxy, and each call already allows longer network latency. The runner should support a timeout value carried by the command plan metadata/config, with a larger default for `demo_worker` or model-backed local execution.

Preferred shape:

```text
adapter config / command plan metadata
  → timeout_seconds
  → subprocess_runner(plan)
```

This keeps the default safe for normal commands while letting the demo path opt into realistic latency.

Alternative considered: globally increase the timeout. Rejected because that makes all adapter launches hang longer, including misconfigured commands.

### 4. Add markdown intake without changing the estimator core first

The board should offer:

- multiline markdown textarea for pasted task files
- optional `.md` upload input

The route should normalize input into the same estimation request shape used today. If both text and file are present, the file should either take precedence with clear UI copy or be appended under a separator; the spec should choose one. The design preference is file wins because it gives deterministic behavior for tests and demos.

No new dependency should be required unless the existing FastAPI multipart support is missing from the test environment.

Alternative considered: build a separate markdown estimation endpoint. Rejected for now because the existing form route can normalize form/file input and call the same estimator path.

### 5. Eval files should be behavior-specific and synthetic-safe

Add eval/test coverage around user-visible behavior, not just function internals:

```text
markdown task file
  → estimate form/API
  → task(s) created with estimate/decomposition metadata

budget usage scenario
  → proxy/token turn recording
  → alarms persisted
  → dashboard/session report exposes alarms

Worker timeout scenario
  → failed session evidence stored
  → task remains Estimated/Ready
  → inline board error appears
  → relaunch remains available
```

Demo fixtures must remain obviously synthetic, using DEMO identifiers and 2099 dates where applicable.

Alternative considered: only add unit tests around helper functions. Rejected because the user's concern is demo behavior and UI/API lifecycle semantics.

## Risks / Trade-offs

- **Risk: Some existing tests expect launch failure to set `Blocked`.** → Update tests to distinguish operational failures from true safety/guardrail blocks.
- **Risk: Preserving relaunchability could hide repeated infrastructure failures.** → Persist `launch_error`/`last_launch_failure` evidence and show it inline until a successful launch clears or supersedes it.
- **Risk: Longer Worker timeouts can make tests slow.** → Keep timeout configurable and test with injected runners/fake timeout values, not real sleeps.
- **Risk: Markdown uploads can create ambiguous input precedence.** → Specify deterministic precedence and cover it with tests.
- **Risk: Alarm evals may duplicate existing coverage.** → Focus on behavior slices: generation, deduplication, dashboard visibility, session report visibility, and control-plane/Worker spend separation.
- **Risk: Native usage and proxy-governed launch modes have different evidence sources.** → Keep eval cases for both where behavior differs, and keep model/auth language separated by control-plane versus Worker layer.

## Migration Plan

1. Add tests/evals that encode the intended behavior before changing launch lifecycle code.
2. Introduce recoverable launch-error metadata while keeping existing sanitized launch command evidence.
3. Update board rendering to show recoverable launch errors on launchable task cards.
4. Make Worker timeout configurable for demo/local model-backed execution.
5. Add markdown intake support to the estimate form route and board template.
6. Add/adjust alarm behavior evals and dashboard/session report assertions.
7. Run targeted tests first, then full `pytest`.

Rollback strategy: revert the lifecycle handling and UI additions together. The database metadata additions are additive and can be ignored by older code.

## Open Questions

- Should uploaded `.md` content replace pasted textarea content, or should the route concatenate both? Design preference: file replaces text for deterministic demos.
- Should operational launch errors clear automatically on the next successful launch, or remain as historical metadata with a separate `last_successful_launch_at`? Design preference: overwrite `launch_error`/`last_launch_failure` on each launch attempt and clear current recoverable launch-error metadata on success.
- Which task status should be restored after a failed launch: the exact pre-launch status or always `Estimated`? Design preference: exact pre-launch status.
- Should missing native usage evidence be recoverable for all launch modes, or remain blocking for native-authoritative adapters? Design preference: recoverable operational failure for launchable task lifecycle, but still fail the session and show strong guardrail copy.
