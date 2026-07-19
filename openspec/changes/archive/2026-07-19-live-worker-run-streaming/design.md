## Context

A Worker Run today runs one-shot: `task_launch._run_worker_adapter` (`task_launch.py:595`) calls
`(runner or subprocess_runner)(plan)`, which runs the adapter CLI to completion and returns a
`CompletedProcess`; `_execute_worker_run` then parses `parse_native_usage_evidence(stdout)` and
`_classify_worker_run_result` to set the authoritative token total and the lifecycle transition. The
`worker-run-transparency` timeline (`worker_run_events` table, `db.py:64`;
`task_launch._record_worker_event`) records only coarse control-plane milestones, and the portal
renders them at review time (`routes/react_shell.py:1115` projects a bounded `timeline`;
`SessionReport.jsx` polls `/freshness` every 5s and announces new evidence).

The adapter builders already invoke the CLIs in streaming-JSON modes (Claude Code
`--output-format stream-json`, Codex `--json`, OpenCode `--format json`), but the one-shot runner
discards every line except the final buffer. This change consumes that discarded stream.

## Goals / Non-Goals

**Goals**
- Record incremental, redacted, normalized Worker-layer events during execution, reusing the
  existing timeline table, recorder, and portal projection.
- Present the timeline live while a run is Running, without regressing the dense Session Report's
  stable-reading (announce-then-refresh) behavior.
- Keep token accounting and lifecycle transitions byte-for-byte identical to a non-streamed run.

**Non-Goals**
- Chat / reply / unread / thread semantics (evidence only; supervisor chat is a later, separate
  surface with its own spec).
- Diff viewer, per-tool token attribution, Gemini adapter, ACP, parallel/worktree execution.
- Any change to Tracking Modes, budget enforcement, or launch guardrails.

## Key Decisions

### 1. Streamed events are evidence, not chat
The new `agent_message` / `tool_call` / `token` / `status` events are system-generated run evidence.
They inherit the existing `worker-run-transparency` prohibition on reply/unread/thread semantics.
This is deliberate and forward-looking: it keeps Phase 3's supervisor chat a **separate surface**,
not "talk into the run timeline."

### 2. Streaming adds a live view; it never decides accounting or state
The authoritative Worker execution token total and the lifecycle transition are computed **only**
from the final run evidence, exactly as today. `streaming_runner` is a strict superset of
`subprocess_runner`: it reads stdout line-by-line for the live feed **and** buffers the identical
full stdout/stderr, returning a `CompletedProcess`-shaped result so `parse_native_usage_evidence`
and `_classify_worker_run_result` see byte-for-byte the same input. Malformed or unrecognized lines
are skipped for the feed and cannot fail the run (fallback to buffered-completion behavior). The
`runner` injection seam is preserved so tests drive a scripted fake streaming runner. Net rule: the
cockpit can never make a launch more fragile than it is today.

### 3. Live usage is provisional
If an adapter streams incremental usage, the portal may show a running number, but it is labeled
provisional and is never charged to the budget or persisted as the task actual. The books close once,
at end-of-run.

### 4. One vertical slice, capture-first task order
Because the review UI already renders the timeline, capture-first tasks land value incrementally
inside a single change: richer post-run timelines appear first through the existing view, then the
final task flips on during-run auto-refresh. This gets the de-risking of a split without a second
proposal, and matches the repo's one-journey-per-change cadence.

## Common event vocabulary

`map_stream_event(raw_line) -> CommonEvent | None` on each builder normalizes heterogeneous streams
to one shape recorded via `_record_worker_event(layer="worker_harness")`:

| kind            | source examples                                              | detail (redacted)              |
|-----------------|-------------------------------------------------------------|--------------------------------|
| `agent_message` | Claude `message`/`result`, Codex agent text, OpenCode text  | bounded text summary           |
| `tool_call`     | Claude `tool_use`, Codex tool events, OpenCode tool events  | tool name + redacted short args |
| `token`         | streamed usage deltas (provisional)                          | running totals (display only)  |
| `status`        | start / finish / error markers                               | short status label             |

Redaction reuses `_redact_value`, `redact_native_cli_text`, and prompt-index redaction before persist.

## Transport

A dedicated bounded endpoint `GET /api/sessions/{id}/events?since_id=` (allowlisted fields, capped
lengths/counts) is cheaper to poll than the full workspace-state payload and reuses the
`react_shell.py:1115` bounding helpers. The frontend polls it on the existing 5s `getJSON` timer only
while status is Running (lightweight list auto-refresh), while the dense Session Report body keeps its
announce-then-manual-refresh model.

## Risks

- **Accounting/lifecycle regression** — the core risk. Mitigated by the strict-superset runner, the
  non-regression scenarios in `worker-run-lifecycle`, and gating on the existing
  `governance-integration-smoke` and `estimation-accuracy-tracking` suites.
- **Event volume / redaction leakage** — bounded projection + reuse of existing redaction helpers;
  cap events per response and detail lengths.
- **Per-adapter stream drift** — mappers are small, pure, and covered by golden fixtures per adapter;
  an unknown shape degrades to no event, not a failed run.
