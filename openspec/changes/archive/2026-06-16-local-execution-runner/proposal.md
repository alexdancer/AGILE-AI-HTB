## Why

AGILE-AI-HTB needs to prove it can govern real coding-agent work, not just display a planning board. The first truthful implementation slice is an all-in-one local execution path that connects a local repo, verifies OpenCode through the Harness Proxy, and records token-ledger evidence before expanding into hosted runner/tunnel or dashboard scale views.

## What Changes

- Add an all-in-one local mode, `htb serve --local-runner`, where the Control Plane and Local Runner run on the same machine.
- Add Connected Project setup for a local repo path and lightweight Project Profile detection.
- Add a Local Runner Execution Backend boundary so later split-runner, tunnel-runner, and hosted-sandbox modes can reuse the board contract.
- Add OpenCode as the first verified local Worker Adapter target.
- Require adapter verification to run a sentinel prompt through the real Worker Adapter and prove token usage was recorded as `adapter_verification`.
- Ensure provider API keys remain inside the Harness; Workers receive only a session-scoped Harness key and Harness Proxy base URL.
- Add a read-only first launch proof where OpenCode inspects the connected repo and produces a session report artifact.
- Add write-task launch guardrails for clean git state, task branch creation, Harness-owned commit after verification, optional PR creation, and conservative failure handling.
- Add budget launch behavior where estimates over remaining budget require explicit audited override, while running sessions are not automatically killed mid-task.

## Capabilities

### New Capabilities
- `local-execution-backend`: Connect local repos, detect project profile data, expose project capability states, and run an in-process Local Runner backend from the Control Plane.
- `worker-adapter-verification`: Configure and verify Worker Adapters, starting with OpenCode, by proving real Harness Proxy token tracking before launch.
- `governed-worker-launch`: Launch read-only and write-capable Worker Sessions with repo cleanliness guardrails, task branches, Harness-owned commits, session artifacts, and blocked failure preservation.
- `budgeted-launch-control`: Gate new launches with budget checks and explicit override auditing while allowing already-running tasks to finish.

### Modified Capabilities

None. No existing OpenSpec specs are present.

## Impact

- CLI: add or extend `htb serve --local-runner`.
- Portal/API: add project setup, project capability display, Worker setup/verification, launch/read-only session flow, and blocked failure reporting.
- Persistence: store connected projects, project profiles, runner/backend capabilities, adapter verification results, session-scoped Harness keys, token usage kinds, task branches, commits, artifacts, and budget override audit records.
- Runner/Adapters: add Local Runner Execution Backend abstraction and OpenCode adapter launch/verification path.
- Proxy/Ledger: ensure adapter verification and Worker Session calls are routed through the Harness Proxy and persisted with correct usage labels.
- Git integration: inspect repo state, create task branches for write-capable sessions, run configured verification, create Harness-owned commits, and optionally expose PR creation when `gh` is available.
