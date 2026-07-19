# Playwright Recorded Demo for DEMO_2099

This change adds an unattended, synthetic Playwright end-to-end test that proves the `DEMO_2099_SIMPLE_MD_LINK_CHECKER.md` workflow through the React Portal: a seeded `Estimated` task is launched from the project board, streamed progress is visible while the task is `Running`, the run completes into `Review`, the Session Report shows live and final evidence, and the operator marks the task `Done`, all without invoking a real Worker CLI or exposing secrets.

## Why

`live-worker-run-streaming` added the streaming capture, incremental events endpoint, and live React feed; its `tasks.md` task `5.6` is the remaining Portal E2E verification. We need an executable, recorded browser demo that exercises the entire surface end-to-end so regressions in the live feed, task lifecycle, and Session Report are caught automatically, and so a checked-in screenshot set can illustrate the feature for operators.

## What Changes

- Add `playwright` to the `test` extras in `pyproject.toml` and document Playwright browser installation for local runs.
- Create `tests/e2e/__init__.py`, `tests/e2e/recorded_demo.py`, and `tests/e2e/test_recorded_demo.py`.
- `recorded_demo.py` provides a `RecordedDemo` context manager that builds a throwaway git repo + SQLite database, seeds a connected project, a verified native-usage `opencode` adapter, and a read-only `Estimated` task, then starts a local FastAPI server with `portal_auth_required=False`.
- The server process monkeypatches `foreman_ai_hq.task_launch.streaming_runner` with a `SyntheticStreamRunner` that emits OpenCode-style streaming JSON lines and a final `step_finish` usage event.
- The Playwright test drives Chrome to `/projects/{project_id}/board`, waits for the task card, clicks **Launch**, observes **Running**, waits for live events containing `DEMO streamed progress 2099`, waits for the card to settle in **Review**, opens the Session Report, asserts token evidence, clicks **Mark Done**, and confirms the card lands in **Done**.
- Capture deterministic demo screenshots under `docs/assets/screenshots/playwright-recorded-demo/` and a trace archive on failure under `test-results/`.
- Add CI caching for `~/.cache/ms-playwright` and a `playwright install chromium` step.
- On completion, mark `openspec/changes/live-worker-run-streaming/tasks.md` task `5.6` done and update `5.7` verification notes.

## Capabilities

### New Capabilities

- `playwright-recorded-demo`: an unattended Portal E2E test that proves the full DEMO_2099 worker run lifecycle through synthetic streamed output and checked-in demo assets.

### Modified Capabilities

_None — this change only adds test-only code and generated demo screenshots; it does not change product specs for Worker run lifecycle, transparency, or the React Portal shell._

## Impact

- `pyproject.toml` — add `playwright` to `[project.optional-dependencies] test`.
- `tests/e2e/` — new package with test-only launcher, synthetic runner, and Playwright test.
- `docs/assets/screenshots/playwright-recorded-demo/` — new checked-in demo screenshot directory.
- `.gitignore` — ignore `test-results/` and Playwright trace blobs if outside `docs/assets/screenshots`.
- `.github/workflows/*.yml` — add Playwright browser install and cache steps to the Python test job.
- `openspec/changes/live-worker-run-streaming/tasks.md` — update `5.6` and `5.7` status on green gates.

## Scope

### In scope

- Synthetic streamed Worker Run with `agent_message` and final `token` events.
- Browser assertions for `Running`, `Review`, `Done` columns and live/Session Report evidence.
- Demo screenshot capture.
- No real Worker CLI, no real provider API calls, no secrets.

### Out of scope

- Markdown intake / Task Breakdown Review flow.
- Login flow (`portal_auth_required=False` for this demo).
- Production endpoint, feature flag, fixture hook, or UI redesign.
- Full video recording (trace/screenshots only).

## Architecture

### Seeding the demo state

`RecordedDemo` builds a throwaway environment:

1. `tempfile.TemporaryDirectory()`.
2. `git init`, configure `user.name` and `user.email`, create an initial empty commit so the project has a clean git state.
3. Copy `demo_tasks/DEMO_2099_SIMPLE_MD_LINK_CHECKER.md` into the temp repo as `README.md` and create a minimal `pyproject.toml` so `detect_project_profile` reports `python` + `pytest`.
4. `db.init_db(<tmp>/harness.db)`.
5. `db.upsert_connected_project(..., capability={"state": "launch_ready", "can_launch": True})`.
6. `db.update_worker_adapter("opencode", workdir=..., config={"command": "opencode"}, supported_models=["opencode/gpt-5.1"], is_default=True)`.
7. `db.mark_worker_adapter_verification("opencode", verified=True, evidence={"tracking_mode": "native_usage", "tracking_authoritative": True})`.
8. `db.create_task(description=<short DEMO_2099 summary>, status="Estimated", estimate_tokens=1500, recommended_model="opencode/gpt-5.1", metadata={"read_only": True, "read_only_proof": True, ...})`.

### Injecting the synthetic stream

The browser test cannot pass a `runner` function to the server via HTTP, so the test starts a dedicated FastAPI process and injects the synthetic runner server-side:

- `tests/e2e/demo_server.py` is executed as `python -m tests.e2e.demo_server`.
- It reads a JSON state file pointed to by `DEMO_STATE_FILE` containing `database_path`, `guardrails_path`, `project_id`, and `task_id`.
- Before importing the app factory, it replaces `foreman_ai_hq.task_launch.streaming_runner` with `SyntheticStreamRunner`.
- `SyntheticStreamRunner(plan, on_event)` emits:
  1. `{"type":"text","sessionID":"ses_demo_2099","part":{"type":"text","text":"DEMO streamed progress 2099","sessionID":"ses_demo_2099"}}`
  2. `{"type":"tool","sessionID":"ses_demo_2099","part":{"tool":"write","input":{"prompt":<plan prompt>},"sessionID":"ses_demo_2099"}}`
  3. `{"type":"step_finish","sessionID":"ses_demo_2099","part":{"type":"step-finish","sessionID":"ses_demo_2099","messageID":"msg_demo_2099","model":"opencode/gpt-5.1","tokens":{"total":15,"input":12,"output":3,"reasoning":53},"cost":0}}`
- It returns `{"returncode":0,"stdout":<final line>,"stderr":""}` so `parse_native_usage_evidence` finalizes `actual_tokens` as `15` and the task moves from `Running` to `Review`.
- The tool-call line intentionally contains the launch prompt so the existing prompt-index redaction is exercised and `PROMPT_REDACTED` appears in the persisted event.

### Running the demo server

- `RecordedDemo` finds a free port, sets `DEMO_STATE_FILE`, starts `demo_server.py` with `subprocess.Popen` using the repo `PYTHONPATH`, and polls `GET /api/settings/budget` until `200`.
- `demo_server.py` runs `uvicorn.run(app, host="127.0.0.1", port=<port>, factory=False)` where `app` is built with `Settings(portal_auth_required=False, database_path=..., guardrails_path=..., local_runner_enabled=True)`.

### Browser test flow

1. Build React assets if `frontend/dist/` is missing: `npm --prefix frontend run build`.
2. Start the `RecordedDemo` server.
3. `page.goto(f"http://127.0.0.1:{port}/projects/{project_id}/board")`.
4. Wait for the task card in the **Estimated** column with text matching `Markdown link checker`.
5. Select adapter `opencode` and model `opencode/gpt-5.1` if the dropdown is not already defaulted.
6. Click the **Launch** button.
7. Wait for the card to move to **Running**.
8. Assert the card/task detail shows a live event containing `DEMO streamed progress 2099` and a provisional usage label.
9. Wait for the card to move to **Review** and for `actual_tokens == 15` to appear.
10. Click the task **Session report** link.
11. On `/sessions/{session_id}` wait for the Session Report to load and assert the `Live Worker Run feed` contains `OpenCode message` and `Provisional usage`.
12. Click the **Refresh** (or wait for freshness polling to update) and assert the token log and budget zone reflect the final `15` tokens.
13. Navigate back to the board, click **Mark Done**.
14. Assert the card appears in **Done**.
15. Take named screenshots at each stage and save to `docs/assets/screenshots/playwright-recorded-demo/`.
16. Stop the server.

## Files

- `pyproject.toml`
- `tests/e2e/__init__.py`
- `tests/e2e/recorded_demo.py`
- `tests/e2e/demo_server.py`
- `tests/e2e/test_recorded_demo.py`
- `docs/assets/screenshots/playwright-recorded-demo/` (created on first run)
- `.gitignore`
- `.github/workflows/*.yml`
- `openspec/changes/live-worker-run-streaming/tasks.md`

## Tasks

- [ ] 1. Add `playwright` to `[project.optional-dependencies] test` in `pyproject.toml` and run `uv lock`/`uv sync --extra test`.
- [ ] 2. Add `tests/e2e/__init__.py`.
- [ ] 3. Implement `tests/e2e/recorded_demo.py` (`RecordedDemo`, `SyntheticStreamRunner`, `make_demo_state`, server lifecycle helpers).
- [ ] 4. Implement `tests/e2e/demo_server.py` (read `DEMO_STATE_FILE`, monkeypatch `streaming_runner`, run `uvicorn`).
- [ ] 5. Implement `tests/e2e/test_recorded_demo.py` Playwright test and screenshot helpers.
- [ ] 6. Update `.gitignore` to ignore `test-results/` and Playwright `.png`/`.zip` trace outputs outside `docs/assets/screenshots`.
- [ ] 7. Add Playwright install + `~/.cache/ms-playwright` cache step to the Python test job in CI.
- [ ] 8. Run `uv run pytest tests/e2e/test_recorded_demo.py -q` locally and capture demo screenshots.
- [ ] 9. Run `npm --prefix frontend run check` and `openspec validate --strict`.
- [ ] 10. Update `openspec/changes/live-worker-run-streaming/tasks.md` to mark `5.6` done and refresh `5.7` gate notes.

## Acceptance Criteria

- `tests/e2e/test_recorded_demo.py` passes locally and in CI without any real Worker CLI or API key.
- The browser sees the task move `Estimated → Running → Review → Done`.
- A live event containing `DEMO streamed progress 2099` is visible while the task is `Running`.
- The Session Report shows final `actual_tokens = 15`.
- The tool-call live event redacts the launch prompt (`PROMPT_REDACTED` appears in the event detail).
- Screenshots are written to `docs/assets/screenshots/playwright-recorded-demo/` for each stage.
- `npm --prefix frontend run check` and `uv run pytest -q` remain green.

## Constraints

- No production code changes or new endpoints.
- No changes to `conftest.py` or global pytest fixtures.
- `portal_auth_required=False` and loopback-only binding keep the demo self-contained; this is test-only.
- The demo uses a read-only task so git cleanliness and branch/commit logic are not exercised.
- Keep browser interaction selectors tied to stable text or `data-testid` attributes already present in `Board.jsx`/`SessionReport.jsx` (no test-only IDs in production code).

## Verification / Gates

- `uv run pytest tests/e2e/test_recorded_demo.py -q`
- `uv run pytest -q`
- `npm --prefix frontend run check`
- `openspec validate --strict`

## Risks

- **Flaky browser timing**: mitigate with explicit Playwright waits (`page.wait_for_selector`/`expect`) and generous timeouts for the synthetic run.
- **React build cost**: `npm --prefix frontend run build` adds time; CI should pre-build, and the launcher should skip the build when `frontend/dist/` already exists.
- **Port collisions**: `RecordedDemo` should bind to `127.0.0.1:0` or scan for a free port; `uvicorn` with `port=0` requires reading the bound port from logs, so prefer picking an open ephemeral port before starting.
- **Playwright browser downloads in CI**: cache `~/.cache/ms-playwright` and run `playwright install chromium`.

## References

- `docs/PLAYWRIGHT_RECORDED_DEMO_PLAN.md`
- `demo_tasks/DEMO_2099_SIMPLE_MD_LINK_CHECKER.md`
- `openspec/changes/live-worker-run-streaming/tasks.md`
- `src/foreman_ai_hq/task_launch.py` (`_run_worker_adapter`, `streaming_runner` seam)
- `src/foreman_ai_hq/stream_events.py`
- `src/foreman_ai_hq/worker_adapters.py` (`OpenCodeAdapterBuilder.map_stream_event`)
- `frontend/src/views/Board.jsx`
- `frontend/src/views/SessionReport.jsx`
- `frontend/src/live-events.js` (`drainLiveEvents`)
