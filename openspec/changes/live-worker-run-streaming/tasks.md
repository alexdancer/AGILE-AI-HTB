## 1. Streaming execution — capture (no UI yet)

- [ ] 1.1 Add `src/foreman_ai_hq/stream_events.py`: `streaming_runner(plan, on_event)` using
  `subprocess.Popen`, iterating stdout line-by-line; call `on_event(mapped_event)` per recognized
  line; buffer the full stdout/stderr and return a `CompletedProcess`-shaped result. Mirror
  `subprocess_runner` timeout(124)/OSError(127) handling. Drop-in for the existing `Runner` protocol.
- [ ] 1.2 Add `map_stream_event(self, raw_line) -> CommonEvent | None` to `WorkerAdapterBuilder`
  (base: best-effort generic JSON line) and override for `claude_code` (stream-json
  `message`/`tool_use`/`result`), `codex` (`--json` events), `opencode` (`--format json`). Normalize
  to `{kind: agent_message|tool_call|token|status, title, detail}`; redact via `_redact_value` /
  `redact_native_cli_text` and prompt-index redaction.
- [ ] 1.3 In `task_launch._run_worker_adapter` / `_execute_worker_run`, run the launch through
  `streaming_runner` with an `on_event` closure that calls `_record_worker_event(..., layer="worker_harness")`
  for each mapped event. Leave the final `parse_native_usage_evidence(stdout)` +
  `_classify_worker_run_result` path unchanged. Preserve the `runner` injection seam (tests inject a
  fake streaming runner).

## 2. Incremental fetch — `src/foreman_ai_hq/db.py`

- [ ] 2.1 Add `since_id: int | None` to `list_worker_run_events` (`:1128`): order by `created_at, id`;
  when provided, return only events with `id > since_id`.

## 3. Events endpoint — `src/foreman_ai_hq/routes/sessions.py`

- [ ] 3.1 Add authenticated `GET /api/sessions/{id}/events?since_id=` returning a bounded projection
  of new events (reuse `react_shell.py:1115` `_bounded_scalar` / `_bounded_text`; allowlist
  `created_at`, `id`, `kind`, `layer`, `title`, `detail_summary`; cap event count per response).

## 4. Live portal feed — `frontend/src/views/*`

- [ ] 4.1 In the run timeline (Board.jsx project workspace + the timeline used by SessionReport.jsx),
  while task/run status is `Running`, poll `/api/sessions/{id}/events?since_id=<lastId>` on the
  existing 5s `getJSON` timer; append new events; stop when status leaves `Running`.
- [ ] 4.2 Render the common feed (`agent_message` / `tool_call` / `token` / `status`) as read-only
  evidence (no reply/unread/thread). Label any live usage figure provisional. Keep the Session
  Report's announce-then-manual-refresh freshness behavior for the dense report body.

## 5. Verification

- [ ] 5.1 Unit: golden fixtures of representative stream lines per adapter → `map_stream_event` yields
  the expected normalized events; secret-like content and the launch prompt are redacted.
- [ ] 5.2 Unit: `streaming_runner` buffers stdout identical to `subprocess_runner` for the same
  scripted output, and downstream `parse_native_usage_evidence` returns the same authoritative total;
  a malformed line is skipped without error.
- [ ] 5.3 Integration: launch with an injected fake streaming runner → `worker_run_events` rows appear
  in order with correct kinds/layer; the task still lands in `Review` with the authoritative
  native-usage total; a retryable failure still returns to `Estimated`.
- [ ] 5.4 Non-regression gate: `governance-integration-smoke` and `estimation-accuracy-tracking`
  suites stay green.
- [ ] 5.5 Frontend: while Running, the feed appends streamed events without a manual refresh and
  settles on completion; live usage shows a provisional label; events render as evidence.
- [ ] 5.6 Portal E2E (synthetic): extend the Recorded Demo Run to a governed launch backed by
  synthetic streamed adapter output; assert live events appear during `Running` and settle on
  completion. No real Worker CLI or secrets.
- [ ] 5.7 Gates: `uv run pytest -q`, `npm --prefix frontend run check`,
  `openspec validate live-worker-run-streaming --strict`.
