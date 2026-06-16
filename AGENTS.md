# Agent Instructions

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

Use `pytest` for the Python test suite.
