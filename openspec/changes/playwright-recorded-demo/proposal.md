## Why

`live-worker-run-streaming` added incremental Worker Run events and a live portal feed, but every
test proving it stops at a service boundary. Task 5.6 of that change asks for evidence that an
operator's **browser** actually renders streamed Worker evidence while a task is `Running` — the one
claim the streaming work exists to make, and the one no current test covers. `tests/` has no browser
lane at all: `CONTEXT.md` defines Portal E2E Test, Demo Scenario Catalog, and Recorded Demo Run as
concepts, but no capability spec or code implements them.

This change adds the first browser lane: one unattended, fully synthetic Playwright run that drives
the real React portal against the real FastAPI application and proves live streaming end to end.
Nothing about production behavior changes — the only production-shaped seam is a test-local
monkeypatch of the Worker subprocess runner.

## What Changes

- Add `tests/e2e/` with a test-only launcher (`recorded_demo.py`) that builds the React frontend,
  seeds a temporary Git repository and dedicated database, and starts `create_app` on an ephemeral
  loopback port inside a thread.
- Substitute a `SyntheticStreamRunner` for `foreman_ai_hq.task_launch.streaming_runner` before the
  server starts. It emits a sentinel agent message and a provisional usage line, blocks on a
  test-controlled release gate, then emits a final Claude `result` line. The real launch route,
  background run thread, stream mappers, event persistence, native-usage parser, and Review
  transition all execute unmodified.
- Drive Chromium through normal portal routes only: login, project board, launch, live streamed
  evidence while `Running`, release, `Review`, Session Report, then Mark Done as a labeled synthetic
  automated disposition.
- Add `playwright` to the test extra. No JS test stack, no pytest plugin, no fixtures, no production
  endpoint, flag, or reset/seed hook.

Non-goals: a generic scenario-framework abstraction, screenshot or video publishing, checked-in
showcase images, real Worker CLI tests, SSE, and any new portal layout. Traces and screenshots are
captured on failure only and remain gitignored.

## Contract reconciliation

`CONTEXT.md` already defines this lane, and the proposed first slice **narrows it in two ways that
need an explicit decision** rather than silent divergence:

1. **Fixture readiness.** CONTEXT states the initial fixture is "truthfully `analysis_ready` rather
   than `launch_ready` when no real Worker Adapter has been verified." Proving live streaming
   requires a launchable task, so this change seeds a synthetically verified native-usage Claude Code
   adapter and a `launch_ready` project. That is consistent with the Recorded Demo Run definition,
   which explicitly permits substituting "synthetic provider and Worker responses," but it
   contradicts the sentence above, which was written for the login/board smoke. The spec must scope
   the `analysis_ready` rule to fixtures that do **not** substitute a synthetic Worker, and require
   that synthetic verification be labeled as such wherever it surfaces.
2. **Scenario coverage.** CONTEXT says the first implementation includes "a complete Recorded Demo
   Run of `DEMO_2099_SIMPLE_MD_LINK_CHECKER.md` through Markdown intake, Task Breakdown Review,
   accepted estimation, synthetic governed launch, Review, and Session Report evidence," plus a fast
   login/project/board/logout smoke. This change starts from a test-seeded accepted task, because
   the intake → breakdown → estimation path needs a synthetic Control Plane response fixture and is
   not required to prove live streaming. The full path and the logout smoke become follow-up work.

Both are deliberate scope reductions, not oversights. The alternative — building the Control Plane
fixture now — delays the streaming evidence that motivates the change.

## Capabilities

### New Capabilities

- `recorded-demo-run`: a deterministic unattended browser run of a Demo Scenario that records portal
  behavior without a real provider or Worker CLI. Covers isolation and synthetic-data rules, the
  test-only launcher boundary (no production reset/seed endpoint or weakening environment mode), the
  synthetic Worker substitution seam, required live evidence while `Running`, labeled synthetic
  disposition at Mark Done, and the artifact-labeling rules that keep synthetic output from being
  presented as real verification, token usage, human review, or provider behavior.

### Modified Capabilities

_None._ No existing spec covers Portal E2E Test, Demo Scenario Catalog, or Recorded Demo Run; the
concepts live only in `CONTEXT.md`, whose Portal E2E Test and Recorded Demo Run entries need the two
narrowings recorded above.

## Impact

- Code (all test-only):
  - **NEW `tests/e2e/__init__.py`**.
  - **NEW `tests/e2e/recorded_demo.py`** — `RecordedDemo` context manager: React build, temporary Git
    project, dedicated database, seeded project/adapter/task/budget through normal DB APIs, threaded
    `uvicorn.Server(...).run()` on `127.0.0.1:0`, `SyntheticStreamRunner`, and guaranteed teardown of
    server, patch, and temporary state.
  - **NEW `tests/e2e/test_recorded_demo.py`** — the browser scenario.
  - `pyproject.toml` — `playwright` in the test extra only.
- Production code: unchanged. The patch target is `foreman_ai_hq.task_launch.streaming_runner`
  (`task_launch.py:23` imports it into that namespace; `task_launch.py:622` calls it as a module
  global). `launch_task` exposes a `runner` seam (`task_launch.py:102`) that the HTTP route does not
  forward, which is why the patch is the only seam a browser-driven launch can reach.
- Behavior this test depends on, and would break against if changed:
  - `board_workspace.py:104` derives `live_refresh_enabled` from the `Running` count.
  - `Board.jsx:148` / `Board.jsx:190` poll status at 2500ms and events at 5000ms.
  - `Board.jsx:390` collapses the run timeline inside `<details>`.
  - `react_shell.py:1156` slices the card timeline to `events[-6:]`.
  - `task_launch.py:676` redacts prompt substrings from streamed output.
  - `native_usage.py:164` returns the **first** qualifying usage payload in the stream.
- CI: needs a Node toolchain (React build output is gitignored at `.gitignore:19`) and cached
  Playwright browsers. Browser binaries are not committed.
- Docs: `docs/PLAYWRIGHT_RECORDED_DEMO_PLAN.md` is the implementation plan; `CONTEXT.md` needs the
  two narrowings under Contract reconciliation.
- Bookkeeping: unblocks marking `live-worker-run-streaming` tasks 5.6 and 5.7.
