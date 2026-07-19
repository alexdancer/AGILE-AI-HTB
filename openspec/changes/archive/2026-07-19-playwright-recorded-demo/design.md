## Context

`live-worker-run-streaming` shipped incremental Worker Run events, a bounded `since_id` projection,
and a live board feed. Every test proving it stops at a service boundary: `tests/portal/` and
`tests/workers/` assert on persisted events and parsed usage, never on what an operator's browser
renders. Task 5.6 of that change asks for exactly that missing evidence.

The repository has no browser lane. There is no Playwright dependency, no `tests/e2e/`, no scenario
catalog, and no provider fake — `CONTEXT.md` defines Portal E2E Test, Demo Scenario Catalog, and
Recorded Demo Run as concepts with no implementation behind them. This design covers the first
implementation, deliberately scoped to the streaming proof rather than the full catalog.

Two constraints shape everything below. First, production must gain no test surface: no reset
endpoint, no seed route, no environment mode that weakens behavior. Second, the substitution must be
narrow enough that the governed pipeline — guardrails, budget accounting, stream mapping, redaction,
usage parsing, lifecycle transition — runs its real code path, or the test proves nothing.

## Goals / Non-Goals

**Goals:**

- Prove in a real browser that streamed Worker evidence renders while a task is `Running`, covering
  both an agent message and provisional token usage.
- Prove the authoritative token total still derives from completion evidence, not from a provisional
  streamed value.
- Establish the `tests/e2e/` lane and its isolation discipline at a size the next scenario can reuse.
- Keep production code byte-for-byte unchanged.

**Non-Goals:**

- A generic scenario-framework abstraction. One scenario does not justify a catalog; extract when a
  second scenario shows what actually varies.
- Markdown intake, Task Breakdown Review, and accepted estimation in this recording. They need a
  synthetic Control Plane fixture and are not required for the streaming proof.
- Screenshot or video publishing, checked-in showcase images, and the `docs/assets/screenshots/`
  recording command.
- Real Worker CLI tests, SSE, and any portal layout change.

## Decisions

### D1: Substitute `streaming_runner`, not the HTTP boundary or the adapter

The synthetic seam is a monkeypatch of `foreman_ai_hq.task_launch.streaming_runner` installed before
the server starts serving.

`task_launch.py:23` imports the symbol into the `task_launch` namespace and `task_launch.py:622`
calls it as a module global, so the patch target must be `foreman_ai_hq.task_launch.streaming_runner`.
Patching `foreman_ai_hq.stream_events.streaming_runner` resolves the same object but never affects
the call site — a silent no-op that would leave the test green against a real subprocess launch
attempt.

Two further production symbols are touched by the launcher, and neither substitutes behavior:

- `task_launch._apply_worker_run_outcome` is wrapped by a pass-through observer that calls the
  original, returns its result, and only sets an event so the browser can reload without racing the
  backend. Polling task status from the test was the alternative; it trades a behavior-preserving
  wrapper for timing flakiness, which is the thing this design most wants to avoid.
- `react_shell.react_build_dir` is restored to the real build directory because `tests/conftest.py:16`
  is an autouse fixture pointing every test at a missing build. Without this the server would serve
  the missing-build recovery shell.

Alternatives considered:

- **`launch_task(runner=...)` injection.** `task_launch.py:102` already exposes a `Runner` seam, and
  it is the right seam for service-level tests. The HTTP launch route does not forward it, so a
  browser-driven launch cannot reach it. Rejected as unreachable, not as wrong.
- **A fake Worker CLI executable on `PATH`.** More faithful — it would exercise real `Popen`
  handling — but it requires shipping a script, makes stream timing hard to gate deterministically,
  and varies by platform. Rejected for determinism.
- **Intercepting at the HTTP or DB layer.** Would bypass the mapper, redaction, and usage parser,
  which are precisely the code under test. Rejected.

### D2: Gate the run open with a `threading.Event`, not a sleep

`_start_background_worker_run` (`task_launch.py:452`) runs the Worker in a `threading.Thread` inside
the application process. Running uvicorn as `uvicorn.Server(...).run()` in a thread of the same
process therefore lets the test share `threading.Event` objects with the synthetic runner directly.

The runner sets `entered` after emitting its pre-gate lines and blocks on `release`. The test waits
on `entered`, performs its browser assertions against a genuinely in-flight run, then sets `release`.
A bounded timeout on the gate plus an unconditional release during teardown prevents a failed
assertion from hanging the suite.

This is why `uvicorn.run()` with reload or workers is prohibited: forking would place the monkeypatch
and both events in a different process, breaking the gate and the substitution together.

Note that `entered` proves the runner reached the gate — it says nothing about what the browser has
rendered. Browser assertions still need their own waits (D4).

### D3: Use Claude Code `stream-json` shapes, which are faithful end to end

The scenario uses the `claude_code` adapter and Claude's `--output-format stream-json` shapes. No
real `claude` binary, API key, or provider is involved; only the subprocess seam is substituted.

This choice was made after an earlier OpenCode draft, and it removes a fidelity compromise rather
than adding one. Through `ClaudeCodeAdapterBuilder.map_stream_event` (`worker_adapters.py:295`):

- an assistant event whose `message.content[]` carries `text` → `agent_message`;
- any event with `type == "result"` and a **top-level** `usage` dict → `_token_stream_event`
  (`worker_adapters.py:309`).

Top-level `usage` is exactly what `_token_stream_event` (`worker_adapters.py:1055`) consumes, so a
provisional token event arises from a shape Claude genuinely emits. The OpenCode alternative could
not do this: its `step_finish` reports under `part.tokens`, which matches neither the location nor
the accepted key names, so it maps to a `status` event and yields no token event at all. Proving
live token evidence on OpenCode would have required inventing a top-level `usage` line that real
OpenCode never emits.

The runner emits three lines:

1. an assistant text line carrying the sentinel → `agent_message`;
2. after `stream_more`, a `result` line with top-level `usage` → provisional `token` event;
3. after `release`, the full `result` line — session-bound, model-bound, costed → the authoritative
   completion evidence.

**Consequence worth knowing:** because Claude routes every `result` with usage through
`_token_stream_event`, line 3 also maps to a `token` event rather than a `status` event. The ordered
worker-harness evidence is therefore `agent_message → token → token`, not
`agent_message → token → status` as it would be on OpenCode. Tests assert that ordering directly.

### D4: Accommodate three browser-visibility facts rather than change the UI

These are current implementation details the test must work with. None belong in the spec, and none
justify a UI change to make testing easier.

```
click launch ──▶ board reload ──▶ Running appears ──▶ live_refresh_enabled flips
                                                              │
                                          event-poll effect MOUNTS only here
                                                              │
                                     poll() immediate, then setInterval 5000ms
```

- `board_workspace.py:104` derives `live_refresh_enabled` from `counts["Running"] > 0`. It
  self-enables, so no seeding is required — but only after a reload observes `Running`, behind a
  2500ms status poll and a 5000ms event poll (`Board.jsx:148`, `Board.jsx:190`). Browser waits need
  explicit timeouts of at least 15s; Playwright's default is too tight to be reliable here.
- `Board.jsx:390` renders the timeline inside a collapsed `<details className="task-details">`.
  Playwright treats content in a closed `<details>` as not visible, so the test opens the disclosure
  and reopens it if a board reload collapses it.
- `react_shell.py:1156` slices the card timeline to `events[-6:]`. The synthetic stream stays short
  and adds no filler ahead of the sentinel.

### D5: Keep the sentinel out of the seeded task body

`_redact_stream_value` (`task_launch.py:676`) replaces every prompt-argument substring in streamed
output with `***PROMPT_REDACTED***`. The prompt is the task body. A fixture that helpfully describes
the expected output in the task text would scrub the sentinel from the stream and fail the test for a
reason with no obvious connection to the assertion.

The launcher asserts the inverse explicitly: the seeded task body must not contain the sentinel.

### D6: Keep the provisional usage line unbindable, so it cannot win the final parse

`parse_native_usage_evidence` (`native_usage.py:164`) walks the JSON stream and returns the **first**
qualifying usage payload. The provisional line shares buffered stdout with the completion `result`
event and comes first, so ordering alone does not protect the final total.

It is skipped only because it carries no model binding, no run binding, and no cost — each of which
independently `continue`s the loop. This design makes that deliberate: the provisional line MUST omit
`session_id`, `modelUsage`, and `total_cost_usd`. Dressing it up to look more realistic would make it
the authoritative evidence instead of the completion event.

Note `_native_usage_cost` (`native_usage.py:243`) short-circuits: when `modelUsage` is present it
returns that map's `costUSD` or `None`, ignoring `total_cost_usd`. The completion line therefore
carries `costUSD` inside `modelUsage`, not cost alone.

The failure mode is quiet. Both lines report 15 tokens, so `actual_tokens == 15` would keep passing
while sourcing from the wrong line. The spec requirement "Final total derives from completion
evidence" exists to pin this, and the service-level test asserts provenance — `source.type`,
`source.session_id`, and the bound model — not just the number.

### D7: Seed through DB APIs, and label the synthetic verification

The launcher seeds project, capability, verified adapter, accepted task, and budget through normal
database APIs — never over HTTP, since exposing seeding through the app is precisely what the spec
forbids.

The adapter is recorded as verified with no real CLI behind it. Per the approved narrowing, this is
allowed for a synthetic-Worker fixture and must be labeled synthetic wherever it surfaces. The
`analysis_ready` rule still binds any future fixture that does not substitute a Worker.

## Risks / Trade-offs

- **Flakiness from poll-cadence timing** → Wait on state, never elapsed time: `entered` for the
  runner gate, explicit ≥15s locator timeouts for browser assertions. No `sleep()` anywhere.
- **The provisional line silently becomes authoritative** (D6) → Assert evidence provenance, not
  just the token count; keep the line free of `model`, `sessionID`, and `cost`.
- **UI drift breaks the test opaquely** — a changed selector, a timeline moved out of `<details>`, a
  different poll interval → Anchor assertions on operator-visible text rather than CSS structure
  where possible, and record the depended-upon behaviors in the proposal's Impact section so a
  reviewer touching them sees the coupling.
- **CI lacks Node or cached browsers** → React build output is gitignored (`.gitignore:19`), so CI
  must run the build and cache Playwright browsers explicitly. Without this the failure is a
  confusing missing-asset shell rather than a clear setup error.
- **The faithful Claude shapes are mistaken for evidence a real CLI ran** (D3) → The shapes are
  wire-accurate, which makes the fixture more convincing than it should be. Keep the synthetic
  labeling requirements strict: seeded verification, artifacts, and disposition all say synthetic.
- **This lane grows into a framework prematurely** → One scenario, no abstraction layer. Extract a
  catalog only when a second scenario demonstrates what varies.

## Open Questions

- Should the `tests/e2e/` lane run in the default `uv run pytest -q` suite, or behind a marker or
  separate CI job? It needs a Node build and a browser binary, which makes a bare `pytest` run fail
  on a machine that has neither. Deferring to implementation, but the friction is real for
  contributors and worth settling before a second scenario lands.
- Does `docs/assets/screenshots/` showcase recording remain a goal for a later change, or has the
  README's screenshot need been met another way? Out of scope here either way.
