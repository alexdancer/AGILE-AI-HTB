## Context

The harness already persists Worker Runs with status, command plan, sanitized stdout/stderr, selected adapter/model, tracking mode, metadata, and session/token evidence. Operators still have to infer the sequence of harness decisions from scattered fields. Connected project profiling also exists, but it is shallow: it detects top-level markers, docs, framework hints, and test/run commands. Coding Workers need that context, plus repo instructions and likely entry points, before launch.

## Goals / Non-Goals

**Goals:**
- Add chronological, redacted Worker Run events as the transparent "what happened" surface.
- Show events on existing task/session views rather than creating a new messages product.
- Build and store a Repo Context Brief for connected-project launches.
- Inject the brief into Worker prompts so Workers inspect existing code and follow repo instructions before editing.
- Keep control-plane/orchestrator events distinct from Worker/coding harness evidence.

**Non-Goals:**
- No websocket/live streaming in this slice.
- No general operator chat or arbitrary message threads.
- No rewrite of the agent loop or Worker Adapter architecture.
- No new external observability backend or dependency.
- No automatic whole-repo semantic indexer in the first slice.

## Decisions

### Use structured Worker Run events, not free-form messages

Store redacted event rows linked to a Worker Run. Events have a small shape: timestamp, level, kind, title, and JSON detail. This is enough to explain launch progress, guardrail decisions, repo-context creation, command planning, adapter execution, usage capture, file evidence, review, and retryable failures.

Alternative considered: a generic messages table. Rejected because it implies chat semantics, threading, unread state, and user-authored conversation UX that the current problem does not need.

### Reuse existing Worker Run/session surfaces

Render the timeline inside existing task/session detail pages and session artifacts. The task card can show the latest important event; detailed chronology lives in the report/detail view.

Alternative considered: a separate logs page. Rejected for the first slice because it hides the evidence away from the workflow point where operators need it.

### Build a small Repo Context Brief from existing local files

Extend connected-project profiling into a brief built from existing repo signals:
- AGENTS.md, CLAUDE.md, README, docs/HARNESS.md when present
- manifests such as pyproject.toml, package.json, Cargo.toml, go.mod
- top-level tree and tracked-file summary
- detected languages/frameworks/package managers
- test and run commands
- likely app/test entry points

The brief is bounded and stored as Worker Run metadata/evidence. It is injected into the Worker prompt before the task description.

Alternative considered: full code indexing. Rejected for this slice; the minimal brief gets most of the value without a new index lifecycle.

### Preserve model-layer separation

Control-plane/orchestrator activity includes creating the brief, deciding launch readiness, guardrail checks, and advisory review. Worker/coding harness activity includes OpenCode/Claude Code/Codex command execution and usage evidence. Timeline labels must identify the layer instead of presenting one generic "agent".

## Risks / Trade-offs

- Event spam → keep required event kinds small and render details collapsed by default.
- Secret leakage → reuse existing evidence sanitization and redact event detail JSON before persistence.
- Stale repo context → build the brief at launch time and record source file names/timestamps where cheap.
- Prompt bloat → cap each source section and the final brief; prefer summaries over full file dumps.
- False confidence from shallow context → label it as a brief, not a complete index; Workers still must inspect relevant files before editing.
