## Context

The current harness is documented as a deployable Control Plane with an AGILE Board, Harness Proxy, budget governance, and token accounting. Recent architecture decisions split coordination from execution: the Control Plane coordinates work, while an Execution Backend owns repository access and Worker Adapter launch. The first truthful implementation must prove real local coding-agent governance before building hosted tunnel/sandbox scale features.

The first implementation target is all-in-one local mode: `htb serve --local-runner`. In this mode the Control Plane and Local Runner can share one process, but code should still depend on an `ExecutionBackend` boundary so split runner, tunnel runner, and hosted sandbox can be added later.

## Goals / Non-Goals

**Goals:**

- Add a local Execution Backend that can connect a local repo path and derive a lightweight Project Profile.
- Verify OpenCode as the first launchable Worker Adapter by proving real Harness Proxy token tracking.
- Launch a read-only OpenCode task that inspects the repo and produces a session report artifact.
- Keep provider API keys inside the Harness; Workers only receive session-scoped Harness keys and proxy base URLs.
- Persist project capability, adapter verification state, sessions, token usage, artifacts, and budget override audit records.
- Define write-capable task guardrails for clean git state, task branches, Harness-owned commits, optional PR creation, and blocked failure preservation.

**Non-Goals:**

- Hosted tunnel runner implementation.
- Hosted sandbox execution.
- Full multi-tenant SaaS hardening.
- Mandatory GitHub PR creation.
- Claude Code, Codex, or Hermes launch verification beyond visible non-launchable presets.
- Automatic retries for failed Worker Sessions.

## Decisions

### Decision: Build all-in-one local mode first

Use `htb serve --local-runner` as the first implementation path. The Local Runner runs inside the local Harness process and can access local repos and local CLIs without a tunnel.

Alternatives considered:
- Hosted Control Plane first: better scale demo surface but cannot honestly run local coding agents without a runner.
- Split runner first: closer to hosted architecture but slower to build/debug.

Rationale: local all-in-one mode proves the core product promise fastest: a real Worker is launched, forced through the Harness Proxy, and token spend is recorded.

### Decision: Introduce an ExecutionBackend contract

The AGILE Board and launch flow should talk to an ExecutionBackend abstraction instead of directly shelling out to OpenCode. The initial backend is in-process local execution.

Expected responsibilities:
- validate project path;
- build/update Project Profile;
- report Project Capability;
- detect Worker Adapter capabilities;
- run adapter verification;
- launch read-only and write-capable sessions;
- monitor process exit/logs;
- preserve artifacts and failure state.

Rationale: this keeps the local implementation from becoming a dead-end when split runner, tunnel runner, or hosted sandbox is added.

### Decision: OpenCode is first verified adapter

OpenCode is the first adapter that must become launchable. Claude Code, Codex, and Hermes can appear as first-class presets but remain non-launchable until token-tracking verification passes.

Rationale: the product promise is adapter governance, not generic custom-command launching. Visible but blocked presets demonstrate Launch Guardrails honestly.

### Decision: Adapter verification requires token-ledger proof

Verification must launch the real Worker Adapter with a sentinel prompt, inject Harness Proxy settings, and prove at least one token usage row was recorded as `adapter_verification`.

Install-only checks such as `opencode --version` are useful diagnostics but not launch proof.

### Decision: Provider keys stay inside the Harness

Workers receive only:

- `OPENAI_BASE_URL=<harness proxy>/v1`
- `OPENAI_API_KEY=<session-scoped harness key>`

The Harness owns provider credentials and uses LiteLLM internally.

Rationale: if Workers receive provider keys directly, they can bypass token tracking and the harness thesis fails.

### Decision: First launch proof is read-only

The first real OpenCode launch should inspect the connected repo and write a session report artifact summarizing language, test command, and top-level structure. It should not modify the repo.

Rationale: this proves launch, repo access, proxy routing, and token accounting while avoiding dirty working-tree risk.

### Decision: Write-capable sessions are gated and Harness-owned

Write-capable sessions require a git repo, visible branch, clean working tree, and a task branch. Worker edits on the task branch, but Harness owns final commits after verification passes. PR creation is optional if GitHub remote and authenticated `gh` are available.

Rationale: Workers should not own git history. The Harness should preserve reviewability and verification evidence.

### Decision: Budgets gate launch, not mid-session termination

If an estimate exceeds remaining budget, the Portal must require explicit budget override and audit it. Running Worker Sessions are not automatically killed mid-task for budget overrun; overruns are recorded and alarmed, while manual abort remains available.

Rationale: coding tasks become unreliable if interrupted mid-session. Budget governance should prevent surprise starts and make overruns visible.

## Risks / Trade-offs

- **OpenCode CLI behavior may not support the required non-interactive sentinel flow** → Start with a prototype command that proves exact invocation, env vars, exit behavior, and output capture before integrating deeply.
- **Some Worker Adapters may ignore OpenAI-compatible proxy env vars** → Keep unverified adapters non-launchable and record verification failure reasons.
- **Provider API key bridging can fail locally or on Render** → Reuse existing LiteLLM provider-key bridging and verify with real proxy token rows.
- **Read-only task may still cause file writes if the agent disobeys** → Verification/session report prompts must explicitly forbid file changes; runner should inspect git diff after read-only sessions and mark Blocked if files changed.
- **Long-running Worker process can hang** → Apply wall-clock timeout as a failure reason, preserve logs, and mark Blocked without auto-retry.
- **No test command may exist for write tasks** → Mark verification as missing test command and require manual approval before Harness-owned commit.
- **SQLite schema changes may be broad** → Add focused migrations or initialization paths with tests around persistence behavior.
