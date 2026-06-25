## 1. Worker Run Timeline Persistence

- [x] 1.1 Add a Worker Run event persistence path linked to `worker_runs`, with timestamp, level, kind, layer, title, and redacted JSON detail.
- [x] 1.2 Add DB helpers to create and list Worker Run events in chronological order.
- [x] 1.3 Add redaction coverage for event detail values containing keys, tokens, passwords, authorization headers, and secret-like strings.

## 2. Timeline Emission During Launch

- [x] 2.1 Record timeline events when launch is requested, guardrails pass/fail, command planning completes, and the adapter starts.
- [x] 2.2 Record timeline events for native/proxy usage evidence, file/workdir evidence, successful completion, retryable failures, and hard safety failures.
- [x] 2.3 Ensure control-plane/orchestrator events and Worker/coding harness events are labeled separately.

## 3. Repo Context Brief

- [x] 3.1 Add a bounded Repo Context Brief builder that reads existing repo instruction files, docs, manifests, detected test/run commands, language/framework hints, and likely entry points.
- [x] 3.2 Store the Repo Context Brief and source list as Worker Run evidence.
- [x] 3.3 Inject the Repo Context Brief into Worker launch prompts before task-specific instructions.
- [x] 3.4 Record a timeline event when repo context is built and injected.

## 4. Portal Evidence

- [x] 4.1 Show Worker Run timeline events on existing task/session review surfaces.
- [x] 4.2 Show latest important retryable failure or completion event without requiring raw stdout/stderr reading.
- [x] 4.3 Show Repo Context Brief source list and bounded content in Worker Run/session evidence.

## 5. Verification

- [x] 5.1 Add DB tests for Worker Run event creation, ordering, and redaction.
- [x] 5.2 Add launch tests asserting key timeline events are emitted on success and recoverable failure.
- [x] 5.3 Add Repo Context Brief tests for AGENTS.md/manifest/test-command detection and prompt injection.
- [x] 5.4 Add portal rendering tests for timeline and repo-context evidence.
- [x] 5.5 Run `pytest`.
