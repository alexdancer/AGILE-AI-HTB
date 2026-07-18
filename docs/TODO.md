# Future TODO

Parking lot for ideas I actually want to revisit. This is not a roadmap or a promise; promote an item to OpenSpec or GitHub Issues when it is ready to build.

## Build next

- [ ] **Control Plane OpenRouter + OAuth front door:** replace the paste-an-API-key Control Plane setup with OpenRouter as the recommended default provider — an OAuth PKCE "Connect" button plus a searchable model catalog over the existing OpenAI-compatible transport, keeping direct openai/anthropic/openai-compatible as Advanced options. See `docs/OPENROUTER_CONTROL_PLANE_PLAN.md` for the full plan. Note: this addresses the multi-model/low-friction Control Plane need; it is **not** ACP (which is a Worker Adapter transport, see below).
- [ ] **Portal refresh:** make the project board easier to scan, especially project navigation, worker setup, queue status, review evidence, and empty/error states.
- [x] **Finish React Portal migration:** React owns every canonical operator-facing route (Dashboard, Projects, project workspace, Orchestration Board, Sessions/Session Report, Task Breakdown Review, Project Task History, Alarms inbox, and the full Settings/Setup group); Jinja is retired except for the standalone login page. See `docs/REACT_PORTAL_PARITY_PLAN.md` for the full history.
- [ ] **Full CLI:** turn `foremanctl` into a real terminal product for init, serve, check, projects, board tasks, worker setup, runs, reports, and budget status.
- [ ] **CLI token usage summary:** add `foremanctl` commands to show token usage by run, task, and day for Foreman-governed sessions.
- [ ] **CLI action sign-off:** let operators approve or deny commands/actions requested by Worker CLIs from the terminal, recording the decision as audit evidence without bypassing Harness guardrails.
- [ ] **MCP facade:** explore using this project as an MCP server so other agents can list projects, inspect boards, create/estimate tasks, launch guarded runs, and fetch artifacts without bypassing Harness guardrails.
- [ ] **Agent planning mode:** add a conversational planning workspace where the user can chat with a Harness-owned planning agent, shape ideas into implementation-ready vertical slices, and create reviewed Estimated tasks for the Orchestration Board without bypassing task breakdown, estimation, budget, or launch guardrails.
  - Reference `siteboon/claudecodeui` / CloudCLI (`https://github.com/siteboon/claudecodeui`) for the normal agent-chat experience: project/session list, responsive chat UI, file explorer, git explorer, terminal, CLI selection, and session management. Adapt the feel, but keep Foreman AI HQ's task creation, budget accounting, review, and launch guardrails as the source of truth.
- [ ] **Tool/token map:** visualize which tools and commands a coding agent used, such as `git status`, `grep`, or `rm`, and show token usage tied to those actions.
- [ ] **Coding work cockpit:** evolve the Portal into the place where an operator can do the full coding-work loop: plan, estimate, launch, review diffs and evidence, manage follow-up tasks, inspect reports, and return to project context without falling back to scattered external notes.
- [ ] **Personal token stats:** show a person's token usage by day, with room for useful rollups later.
- [ ] **Diff Viewer:** Have a diff viewer included
- [ ] **Parallel task communication:** provide a way for multiple Tasks running in parallel to exchange status, findings, and handoff notes without bypassing Harness guardrails.
- [ ] Revisit Hermes Worker Adapter support later: define a correct non-interactive command shape, prove selected-model verification, and only restore it after trustworthy run-bound usage evidence is available.
- [ ] **ACP Worker Adapter transport:** explore adding an Agent Client Protocol (Zed's JSON-RPC-over-stdio standard) adapter kind alongside the current template-based command builders, so ACP-capable agents (Claude Code, Gemini) auto-negotiate sessions/models instead of hand-written launch/verification templates. ACP is a control/observe protocol, not a token-accounting one: it upgrades the launch, streamed tool-call, permission (→ HITL/Escalation), and cancellation layers, but must sit on top of existing Tracking Modes — an ACP session still needs `proxy_governed` or `native_usage` underneath to stay budget-authoritative, or it degrades to `observed_only`. Add it as a new adapter transport, not a replacement for the Setup tab; keep OpenCode-first launch proof intact since OpenCode/Codex do not speak ACP natively. Note: ACP is a **Worker Adapter** transport and does not touch the Control Plane orchestration model — the low-friction multi-model Control Plane need is handled separately by `docs/OPENROUTER_CONTROL_PLANE_PLAN.md`.
- [ ] Make budget reporting more useful: estimated vs. actual tokens, orchestration vs. Worker tokens, and native-usage override evidence.
- [ ] **Estimate vs actual breakdown:** show where a task's real token usage diverged from the estimate, with a short explanation panel.
- [ ] Keep Task Breakdown focused on small vertical slices plus a final Acceptance Verification task for integrated features.
- [ ] Make Agent Review and Worker Run evidence easier to compare from the Portal and CLI.
- [ ] **Linear MCP connection:** explore connecting to Linear via its MCP server as an alternative way to sync/import tasks, instead of (or alongside) GitHub Issues, without bypassing task breakdown, estimation, or launch guardrails.

## MCP notes

- [ ] Use `docs/MCP_AGENT_HARNESS_TODO.md` before implementing the MCP slice.
- [ ] Start with local stdio MCP over existing Control Plane paths; no new orchestration engine.
- [ ] When designing the MCP/token-compression slice, include an explicit optional choice to evaluate Headroom (`https://github.com/headroomlabs-ai/headroom`) for tool output, log, file, and RAG chunk compression; keep it optional and separate from the required Foreman AI HQ install path.
- [ ] Do not expose shell, raw SQL, secrets, or any launch path that skips `task_launch` guardrails.

## Later, only if usage proves it

- [ ] Hosted workspace/sandbox execution with isolation, credentials policy, adapter install, and launch proof.
- [ ] Hosted Streamable HTTP MCP with scoped auth.
- [ ] Per-project permissions for read, task-write, launch, review, and admin.
- [ ] Pagination/audit events for large logs, artifacts, and mutating facade calls.
