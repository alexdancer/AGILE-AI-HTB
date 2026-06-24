## Context

The project workspace entry change makes `/projects/{project_id}` the natural portal context for a repo. Current Worker Adapter setup still has a separate `workdir` field, and Local Runner project connect currently configures OpenCode's adapter workdir directly. That duplicates repo selection and makes operators think they must configure a project twice.

Worker Adapters should remain local CLI integrations: OpenCode, Claude Code, Codex, Hermes, etc. Tracking mode remains separate: `proxy_governed`, `native_usage`, or `observed_only`. The repo/project boundary should come from the active project workspace, not from each adapter's settings form.

## Goals / Non-Goals

**Goals:**
- Use the active/selected connected project root as the default Worker launch workdir.
- Keep Worker Adapter settings focused on CLI availability, auth/native configuration, model discovery, verification, default adapter selection, and tracking mode.
- Require normal board launches to have a connected active project root before starting a Worker run.
- Preserve OpenCode's explicit project-directory binding with `opencode run --dir {active_project.root_path}`.
- Avoid a schema migration unless implementation proves a persisted active-project pointer is unavoidable.

**Non-Goals:**
- No project-scoped board/session/report filtering in this change.
- No new Worker Adapter identities or tracking modes.
- No change to model routing, budget accounting semantics, or native usage authority checks.
- No file picker or SPA project switcher.

## Decisions

1. **Project root comes from connected project state, not Worker Adapter config.**
   - Board launch should resolve a connected project root and pass it into launch planning.
   - Worker Adapter rows can still keep legacy `workdir` for compatibility/diagnostics, but normal board launches should not require the operator to enter it.
   - Alternative: keep syncing every adapter's `workdir` when the active project changes. Rejected because it preserves duplicate state and can drift.

2. **Use most-recent connected project as the first active-project rule.**
   - The previous change already redirects login to the most recent project.
   - For the first implementation slice, board launch can use the most recent connected project when no explicit project context is otherwise present.
   - Alternative: add a persisted active project preference. Defer until there is a real switch-project use case that needs it.

3. **Board launch guardrail owns the missing-project failure.**
   - If no connected project exists, launch should fail before Worker process creation with a clear link to `/projects`.
   - This is a workflow/setup guardrail, not a Worker runtime failure and not a reason to mark a task Blocked automatically.
   - Alternative: let adapters fall back to process cwd. Rejected because it can edit the harness repo or the wrong repo.

4. **OpenCode must receive explicit `--dir`.**
   - Subprocess `cwd` alone is not enough proof that OpenCode edited the intended repo.
   - Launch command planning should bind OpenCode with `--dir {project_root}` and record that configured workdir in evidence.
   - Alternative: rely on cwd and post-run inspection. Rejected as weaker and already known to be misleading.

5. **Verification remains adapter-level.**
   - Adapter verification proves the CLI and tracking mode can produce trustworthy evidence.
   - It does not select a project workspace and should not be presented as project configuration.
   - Normal board launch requires both a verified launchable adapter and a connected project root.

## Risks / Trade-offs

- Existing code/tests may expect `worker_adapters.workdir` to be the launch root. → Keep legacy field readable while changing normal launch planning to prefer connected project root.
- Multiple connected projects can make "active" ambiguous outside `/projects/{id}`. → Use most-recent connected project for the first slice and leave explicit persisted active selection for a later change.
- Removing the workdir input too aggressively may hide useful diagnostics. → De-emphasize normal workdir config, but keep diagnostic evidence/copy where needed.
- OpenCode command templates may already include or omit `--dir`. → Normalize command planning so exactly the selected project root is bound and test the command plan.
