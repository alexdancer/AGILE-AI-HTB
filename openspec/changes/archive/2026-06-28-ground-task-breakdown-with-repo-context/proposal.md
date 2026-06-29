## Why

Task Breakdown currently slices Markdown or oversized work mostly from the submitted text plus light project metadata, while estimation and Worker launch already use the connected repo's bounded Repo Context Brief. This can produce generic AGILE Board cards even when the Control Plane already has enough project context to make repo-aware implementation slices.

## What Changes

- Feed the existing bounded Repo Context Brief into the Task Breakdown Agent for connected-project intake.
- Keep global/no-project breakdown behavior unchanged.
- Preserve the existing human Proposed Task Breakdown review flow before AGILE Board Tasks are created.
- Store enough breakdown metadata to audit which repo context was used, without dumping the whole repository or adding a new indexer.
- Do not add embeddings, RAG, AST indexing, or full-repo prompt dumps.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `task-breakdown-review`: Task Breakdown Agent proposals for connected-project intake are grounded with bounded Repo Context Brief information before operators accept implementation and Acceptance Verification cards.

## Impact

- Affected code: `src/agile_ai_htb/routes/tasks.py`, `src/agile_ai_htb/task_breakdown.py`, `src/agile_ai_htb/repo_context.py` reuse points, and Task Breakdown tests.
- Affected product surfaces: Proposed Task Breakdown review records and review evidence metadata.
- Dependencies: none.
- Verification: targeted Task Breakdown tests plus `uv run pytest`.
