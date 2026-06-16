## 1. Project connection and local runner foundation

- [x] 1.1 Add persistence for Connected Project, lightweight Project Profile, Project Capability, Execution Backend status, and Worker Adapter verification state.
- [x] 1.2 Add `--local-runner` support to the `htb serve` CLI path and settings so the local Execution Backend can be enabled explicitly.
- [x] 1.3 Implement a local `ExecutionBackend` service boundary that validates local project paths, reports capabilities, and can be called by portal/task launch code without directly shelling out from routes.
- [x] 1.4 Implement Project Profile detection for local paths: project name, root path, git branch when present, language/framework/package-manager hints, test command, run command when obvious, top-level folders, and relevant docs.
- [x] 1.5 Add Project Setup API/Portal flow to connect a local repo path, show validation errors, display the detected Project Profile, and show Project Capability.
- [x] 1.6 Add tests for valid project connection, invalid path rejection, profile detection, and capability state display.

## 2. OpenCode adapter verification

- [x] 2.1 Add OpenCode as a first-class Worker Adapter preset while keeping Claude Code, Codex, and Hermes visible but non-launchable until verified.
- [x] 2.2 Implement OpenCode detection diagnostics separately from launch verification, including installed/callable status and clear failure reasons.
- [x] 2.3 Implement session-scoped Harness key issuance for adapter verification and Worker launch.
- [x] 2.4 Implement OpenCode verification launch that injects Harness Proxy base URL and session-scoped Harness key, runs the sentinel prompt, captures output/exit status, and forbids file/tool activity for verification.
- [x] 2.5 Persist verification token usage as `adapter_verification` orchestration spend and mark OpenCode launchable only when token-ledger evidence exists.
- [x] 2.6 Add tests proving install-only checks do not mark an adapter launchable, direct proxy calls do not mark an adapter launchable, successful sentinel verification does, and provider API keys are not passed into Worker env.

## 3. Read-only governed launch proof

- [x] 3.1 Add a read-only session launch path for the Local Runner backend that starts OpenCode in the connected repo and routes model traffic through the Harness Proxy.
- [x] 3.2 Add the first proof task prompt: inspect the connected repo and produce a session report artifact with language, test command, and top-level structure.
- [x] 3.3 Persist session lifecycle, logs, Worker token usage, session report artifact, process exit status, and failure reason when present.
- [x] 3.4 Detect unexpected file changes after read-only sessions and mark the session Blocked while preserving diff evidence.
- [x] 3.5 Add Portal affordance to launch the read-only proof only when Project Capability is Launch-ready via Local Runner and OpenCode is verified.
- [x] 3.6 Add tests for successful read-only proof, blocked launch when adapter is unverified, blocked session when no model call is observed, and blocked session when read-only execution modifies files.

## 4. Write-capable session guardrails

- [x] 4.1 Add read-only vs write-capable task classification to launch requests and Task/session records.
- [x] 4.2 Implement Repository Cleanliness Guardrail for write-capable sessions: require git repo, visible current branch, and clean working tree before launch.
- [x] 4.3 Implement task branch creation using `htb/task-<id>-<slug>` after cleanliness guardrails pass.
- [x] 4.4 Implement post-run verification using the Project Profile test command when configured and capture exit code/output summary.
- [x] 4.5 Implement Harness-generated git diff review summary after Worker changes.
- [x] 4.6 Implement Harness-owned commit after tests pass and diff summary exists; if no test command exists, require manual approval before commit.
- [x] 4.7 Preserve uncommitted changes and mark Blocked when verification fails.
- [x] 4.8 Add optional Open PR action only when GitHub remote and authenticated `gh` CLI are available; lack of PR capability must not block local completion.
- [x] 4.9 Add tests for dirty repo blocking write launch, task branch creation, commit gating, missing-test manual approval requirement, verification failure preservation, and optional PR capability detection.

## 5. Budgeted launch behavior

- [x] 5.1 Add launch-time budget check that compares Task estimate against remaining budget before Worker launch.
- [x] 5.2 Implement explicit budget override flow: normal Launch blocked, `Launch with budget override` shown, `budget_override=true` recorded, and approval audited.
- [x] 5.3 Ensure running sessions are not automatically killed for budget overrun; record overrun and raise alarm while allowing completion unless manually aborted.
- [x] 5.4 Implement manual abort path that stops the Worker process and preserves logs, token ledger entries, branch name, diff, and abort reason.
- [x] 5.5 Add tests for estimate-within-budget launch, estimate-over-budget override requirement, override audit persistence, overrun recording without auto-kill, and manual abort preservation.

## 6. End-to-end verification and documentation

- [x] 6.1 Add or update docs for local mode: `htb serve --local-runner`, connecting a local repo, verifying OpenCode, running the read-only proof, and interpreting capability states.
- [x] 6.2 Add a local smoke test or scripted verification that exercises project connection, OpenCode verification with token-ledger evidence, and read-only proof artifact generation where OpenCode is available.
- [x] 6.3 Run targeted tests for new project/backend/adapter/session/budget behavior.
- [x] 6.4 Run full `pytest` and fix regressions.
- [x] 6.5 Update `docs/HARNESS.md` and `CONTEXT.md` if implementation discovers contract drift.
