## Why

Operators need to see what the harness is doing during a Worker launch without reading raw stdout or guessing from task status. Worker launches also need better repo awareness so coding agents inspect existing project instructions, manifests, entry points, and tests before editing.

## What Changes

- Add a Worker Run timeline: redacted, chronological events for launch, guardrail, repo-context, command, adapter, usage, file-evidence, review, completion, and failure steps.
- Show the timeline on existing task/session surfaces instead of adding a separate messaging product.
- Add a Repo Context Brief built from the connected project before launch.
- Store the brief as Worker Run evidence and inject it into Worker launch prompts.
- Keep control-plane/orchestrator activity separate from Worker/coding harness activity in labels and evidence.

## Capabilities

### New Capabilities
- `worker-run-transparency`: Worker Runs expose a redacted event timeline so operators can understand harness decisions, launch progress, failures, and retryability.
- `repo-context-awareness`: Connected project launches include a stored Repo Context Brief built from existing repo instructions, docs, manifests, tests, and likely entry points.

### Modified Capabilities
- `worker-run-lifecycle`: Worker Run lifecycle views include timeline evidence and repo-context evidence as part of launch/review diagnostics.
- `governed-worker-launch`: Worker launch prompts include the Repo Context Brief before task-specific instructions.

## Impact

- Affected code: Worker Run persistence, launch orchestration, portal task/session views, Worker prompt construction, tests.
- No new external dependencies.
- No new chat/messaging subsystem, websocket stream, or agent-loop rewrite in this slice.
