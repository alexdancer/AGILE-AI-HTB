# Agent Instructions

## Agent skills

### Issue tracker

This repo tracks work in GitHub Issues for `alexdancer/AGILE-AI-HTB`. Use the `gh` CLI when creating or updating issues.

### Triage labels

Use the default triage vocabulary unless repo labels say otherwise:

- `needs-triage` — maintainer needs to evaluate
- `needs-info` — waiting on reporter
- `ready-for-agent` — fully specified and ready for an AFK agent
- `ready-for-human` — needs human implementation or decision
- `wontfix` — will not be actioned

### Domain docs

This is a single-context repo. Read `CONTEXT.md` before making product, architecture, workflow, or terminology changes. Treat it as the source of truth for Harness, Control Plane, Worker Adapter, Orchestration Board, budget governance, and demo vocabulary.

## OpenSpec workflow

This repo uses OpenSpec for spec-driven planning. OpenSpec is initialized under `openspec/` and the CLI is available as `openspec`.

When the user asks to explore, propose, implement, sync, or archive OpenSpec changes, use the matching Hermes skill if available:

- `openspec-explore` — think through ideas, investigate the codebase, and clarify requirements without implementing.
- `openspec-propose` — create a new OpenSpec change and generate proposal/design/spec/tasks artifacts.
- `openspec-apply-change` — implement tasks from an existing OpenSpec change.
- `openspec-sync-specs` — merge delta specs from a change into main specs.
- `openspec-archive-change` — finalize and archive a completed OpenSpec change.

OpenSpec CLI commands to prefer:

- `openspec list --json` to inspect active changes.
- `openspec status --change "<name>" --json` to resolve planning paths and artifact state.
- `openspec instructions <artifact-id> --change "<name>" --json` before writing artifacts.
- `openspec instructions apply --change "<name>" --json` before implementing tasks.

Do not assume repo-local paths for OpenSpec artifacts. Use `planningHome`, `changeRoot`, `artifactPaths`, `contextFiles`, and `actionContext` from the CLI JSON output.

For implementation work, keep changes minimal, run targeted tests, then mark completed OpenSpec tasks with `- [x]` only after verification passes.

## Project verification

Use `uv run pytest` for the Python test suite when using the repo-managed uv environment. If the environment is already active and dependencies are installed, `pytest` is acceptable.
