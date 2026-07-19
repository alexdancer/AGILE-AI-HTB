## Why

Worker Runs execute one-shot and invisibly: `task_launch._run_worker_adapter` runs the coding CLI
to completion through `subprocess_runner`, then parses usage. The `worker-run-transparency` timeline
records only coarse control-plane milestones (launch request, guardrail result, command planning,
adapter start, completion). An operator sees a Running task, then a finished one — never the agent
working. The reference cockpits this roadmap targets (firstmate, compozy) get their value from live
run visibility; the harness already has the governed pipeline they lack, but not the live view.

The adapters already emit streaming JSON (Claude Code `stream-json`, Codex `--json`, OpenCode
`--format json`); the harness throws the intermediate lines away. This change reads that stream
incrementally into the existing `worker_run_events` timeline and presents it live — with **no new
protocol** (ACP considered and deferred; see `docs/LIVE_RUN_COCKPIT_PLAN.md`) and **no change to
budget authority**. It is Phase 1 of a cockpit → fleet → chat roadmap.

## What Changes

- Read the Worker Adapter's streamed stdout **incrementally during the run** and record redacted,
  normalized timeline events as they arrive — a common vocabulary across all adapters: agent message
  (text/reasoning), tool call (name + redacted args), provisional usage, and status — in addition to
  the existing control-plane milestones.
- Normalize per-adapter stream shapes through small per-builder mappers; unrecognized or malformed
  lines are omitted from the feed and never fail the run.
- Present the timeline **live in the portal while a task/run is Running** (auto-refresh), settling on
  completion. The dense Session Report keeps its announce-then-manual-refresh freshness model.
- Any usage figure shown during the run is **labeled provisional**; the authoritative Worker
  execution token total remains the one finalized when the run completes.
- Streaming is **additive**: the full stdout is still buffered and parsed by the same end-of-run
  path, so token accounting and lifecycle transitions (Running→Review, retryable→Estimated) are
  byte-for-byte unchanged.

Non-goals: operator chat / reply / unread / thread semantics on timeline events (evidence only; the
supervisor chat is a separate future surface); a diff viewer; per-tool token attribution
(tool/token-map); a Gemini adapter or any ACP client; parallel / worktree execution; any change to
Tracking Modes, budget enforcement, or launch guardrails.

## Dependencies

- Builds on the existing `worker-run-transparency` timeline (the `worker_run_events` table, its
  recorder, and the portal projection) and `worker-run-lifecycle` finalization. No new provider,
  schema, or migration.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `worker-run-transparency`: the timeline additionally records incremental streamed Worker-layer
  events during execution, and the portal presents them live while Running; a live usage figure is
  provisional until finalized. The existing redaction and evidence-not-chat guarantees extend to the
  new events.
- `worker-run-lifecycle`: gains a non-regression invariant — the authoritative token total and the
  lifecycle transition are derived from the same final run evidence whether or not events were
  captured incrementally.
- `react-portal-shell`: gains a bounded, authenticated incremental projection for live Worker Run
  events (allowlisted fields, capped lengths/counts, `since_id` cursor).

## Impact

- Code:
  - **NEW `src/foreman_ai_hq/stream_events.py`** — `streaming_runner(plan, on_event)` (`Popen`,
    line-by-line, buffers the full stdout/stderr, returns a `CompletedProcess`-shaped result;
    mirrors `subprocess_runner` timeout(124)/OSError(127) handling; drop-in for the `Runner` protocol).
  - `src/foreman_ai_hq/worker_adapters.py` — `map_stream_event` on `WorkerAdapterBuilder` plus
    overrides for `ClaudeCodeAdapterBuilder` / `CodexAdapterBuilder` / `OpenCodeAdapterBuilder`;
    reuse `_redact_value`, `redact_native_cli_text`, and prompt-index redaction.
  - `src/foreman_ai_hq/task_launch.py` — `_run_worker_adapter` / `_execute_worker_run` pass an
    `on_event` closure to `_record_worker_event`; the final `parse_native_usage_evidence` +
    `_classify_worker_run_result` path is unchanged; the `runner` injection seam is preserved.
  - `src/foreman_ai_hq/db.py` — `list_worker_run_events(..., since_id)` incremental fetch (`:1128`).
  - `src/foreman_ai_hq/routes/sessions.py` — `GET /api/sessions/{id}/events?since_id=` bounded
    projection (reuse the `react_shell.py:1115` truncation/redaction helpers).
  - `frontend/src/views/*` (Board.jsx and the run timeline used by SessionReport.jsx) — poll the
    events endpoint while Running (the existing 5s `getJSON` pattern), append and render the common
    feed; provisional label on live usage.
- Database: none new — reuses `worker_run_events` (`db.py:64`) and its recorder.
- Docs: `docs/LIVE_RUN_COCKPIT_PLAN.md` is the roadmap; `docs/TODO.md` line 22 already repointed.
