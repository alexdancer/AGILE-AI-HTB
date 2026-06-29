## 1. Breakdown Input

- [x] 1.1 Extend `breakdown_task_source()` to accept optional structured repo context while keeping existing callers backward-compatible.
- [x] 1.2 Include repo context as a separate request field from `source_text`, `intake_metadata`, and `structure_hints`.
- [x] 1.3 Update the Task Breakdown Agent system prompt to use repo context only for grounding candidate slices, verification commands, entrypoints, and constraints.

## 2. Connected Project Wiring

- [x] 2.1 In the task intake breakdown path, build `build_repo_context_brief(project_root_path)` only when intake metadata points to a connected project root.
- [x] 2.2 Fall back to no-context breakdown when the project root is missing or unreadable.
- [x] 2.3 Store bounded repo-context evidence/source metadata on the Proposed Task Breakdown record when context is used.

## 3. Tests and Verification

- [x] 3.1 Add a project-bound Markdown breakdown test proving the LLM request includes repo context and keeps source text separate.
- [x] 3.2 Add a global/no-project breakdown test proving no repo context is sent.
- [x] 3.3 Add or update a review-record test proving repo-context evidence is stored redacted/bounded.
- [x] 3.4 Run targeted Task Breakdown tests and `uv run pytest`.
