# Future TODO

Parking lot for ideas I actually want to revisit. This is not a roadmap or a promise; promote an item to OpenSpec or GitHub Issues when it is ready to build.

## Build next

- [ ] **Portal refresh:** make the project board easier to scan, especially project navigation, worker setup, queue status, review evidence, and empty/error states.
- [ ] **Revamped Frontend:** change the frontend to have more general quality using React or Svelte
- [ ] **Full CLI:** turn `htb` into a real terminal product for init, serve, check, projects, board tasks, worker setup, runs, reports, and budget status.
- [ ] **CLI token usage summary:** add `htb` commands to show token usage by run, task, and day for HTB-governed sessions.
- [ ] **CLI action sign-off:** let operators approve or deny commands/actions requested by Worker CLIs from the terminal, recording the decision as audit evidence without bypassing Harness guardrails.
- [ ] **MCP facade:** explore using this project as an MCP server so other agents can list projects, inspect boards, create/estimate tasks, launch guarded runs, and fetch artifacts without bypassing Harness guardrails.
- [ ] **Agent planning mode:** add a conversational planning workspace where the user can chat with a Harness-owned planning agent, shape ideas into implementation-ready vertical slices, and create reviewed Estimated tasks for the AGILE Board without bypassing task breakdown, estimation, budget, or launch guardrails.
  - Reference `siteboon/claudecodeui` / CloudCLI (`https://github.com/siteboon/claudecodeui`) for the normal agent-chat experience: project/session list, responsive chat UI, file explorer, git explorer, terminal, CLI selection, and session management. Adapt the feel, but keep AGILE-AI-HTB's task creation, budget accounting, review, and launch guardrails as the source of truth.
- [ ] **Tool/token map:** visualize which tools and commands a coding agent used, such as `git status`, `grep`, or `rm`, and show token usage tied to those actions.
- [ ] **Coding work cockpit:** evolve the Portal into the place where an operator can do the full coding-work loop: plan, estimate, launch, review diffs and evidence, manage follow-up tasks, inspect reports, and return to project context without falling back to scattered external notes.
- [ ] **Personal token stats:** show a person's token usage by day, with room for useful rollups later.
- [ ] **Diff Viewer:** Have a diff viewer included
- [ ] **Parallel task communication:** provide a way for multiple Tasks running in parallel to exchange status, findings, and handoff notes without bypassing Harness guardrails.
- [ ] Revisit Hermes Worker Adapter support later: define a correct non-interactive command shape, prove selected-model verification, and only restore it after trustworthy run-bound usage evidence is available.
- [ ] Make budget reporting more useful: estimated vs. actual tokens, orchestration vs. Worker tokens, and native-usage override evidence.
- [ ] **Estimate vs actual breakdown:** show where a task's real token usage diverged from the estimate, with a short explanation panel.
- [ ] Keep Task Breakdown focused on small vertical slices plus a final Acceptance Verification task for integrated features.
- [ ] Make Agent Review and Worker Run evidence easier to compare from the Portal and CLI.

## MCP notes

- [ ] Use `docs/MCP_AGENT_HARNESS_TODO.md` before implementing the MCP slice.
- [ ] Start with local stdio MCP over existing Control Plane paths; no new orchestration engine.
- [ ] When designing the MCP/token-compression slice, include an explicit optional choice to evaluate Headroom (`https://github.com/headroomlabs-ai/headroom`) for tool output, log, file, and RAG chunk compression; keep it optional and separate from the required AGILE-AI-HTB install path.
- [ ] Do not expose shell, raw SQL, secrets, or any launch path that skips `task_launch` guardrails.

## Later, only if usage proves it

- [ ] Hosted workspace/sandbox execution with isolation, credentials policy, adapter install, and launch proof.
- [ ] Hosted Streamable HTTP MCP with scoped auth.
- [ ] Per-project permissions for read, task-write, launch, review, and admin.
- [ ] Pagination/audit events for large logs, artifacts, and mutating facade calls.
