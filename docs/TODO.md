# Future TODO

Parking lot for ideas I actually want to revisit. This is not a roadmap or a promise; promote an item to OpenSpec or GitHub Issues when it is ready to build.

## Build next

- [ ] **Portal refresh:** make the project board easier to scan, especially project navigation, worker setup, queue status, review evidence, and empty/error states.
- [ ] **Revamped Frontend:** change the frontend to have more general quality using React or Svelte
- [ ] **Full CLI:** turn `htb` into a real terminal product for init, serve, check, projects, board tasks, worker setup, runs, reports, and budget status.
- [ ] **MCP facade:** explore using this project as an MCP server so other agents can list projects, inspect boards, create/estimate tasks, launch guarded runs, and fetch artifacts without bypassing Harness guardrails.
- [ ] **Tool/token map:** visualize which tools and commands a coding agent used, such as `git status`, `grep`, or `rm`, and show token usage tied to those actions.
- [ ] **Personal token stats:** show a person's token usage by day, with room for useful rollups later.
- [ ] **Diff Viewer:** Have a diff viewer included

## Fix the sharp edges

- [ ] Make budget reporting more useful: estimated vs. actual tokens, orchestration vs. Worker tokens, and native-usage override evidence.
- [ ] Keep Task Breakdown focused on small vertical slices plus a final Acceptance Verification task for integrated features.
- [ ] Make Agent Review and Worker Run evidence easier to compare from the Portal and CLI.

## MCP notes

- [ ] Use `docs/MCP_AGENT_HARNESS_TODO.md` before implementing the MCP slice.
- [ ] Start with local stdio MCP over existing Control Plane paths; no new orchestration engine.
- [ ] When designing the MCP/token-compression slice, include an explicit optional choice to evaluate Headroom (`https://github.com/headroomlabs-ai/headroom`) for tool output, log, file, and RAG chunk compression; keep it optional and separate from the required AGILE-AI-HTB install path.
- [ ] Do not expose shell, raw SQL, secrets, or any launch path that skips `task_launch` guardrails.

## Keep honest

- [ ] Demos stay synthetic end-to-end: DEMO banner, 2099 dates, 999-style IDs, `.invalid` emails, and fake addresses.
- [ ] Add invariant tests before adding new demo data.
- [ ] For demo work: write the script/docs first, implement second, verify locally with Docker, then record or deploy.

## Later, only if usage proves it

- [ ] Hosted workspace/sandbox execution with isolation, credentials policy, adapter install, and launch proof.
- [ ] Hosted Streamable HTTP MCP with scoped auth.
- [ ] Per-project permissions for read, task-write, launch, review, and admin.
- [ ] Pagination/audit events for large logs, artifacts, and mutating facade calls.
