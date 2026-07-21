## 1. Browser dependency

- [x] 1.1 Add `playwright` to the test extra in `pyproject.toml`; add no JS test stack, pytest plugin, or pytest configuration
- [x] 1.2 Verify setup: `uv sync --extra test`, `uv run playwright install chromium`, and `uv run python -c 'from playwright.sync_api import sync_playwright'`
- [x] 1.3 Confirm `npm --prefix frontend run build` produces servable assets, and note in the change that CI needs both a Node toolchain and cached Playwright browsers (build output is gitignored at `.gitignore:19`)

## 2. Recorded Demo launcher

- [x] 2.1 Create `tests/e2e/__init__.py` and `tests/e2e/recorded_demo.py`
- [x] 2.2 Implement the `RecordedDemo` context manager: temporary `DEMO_999_mdlink_project` Git repo with minimal synthetic files, dedicated database, dedicated portal token
- [x] 2.3 Seed project, capability, synthetically verified native-usage Claude Code adapter, accepted task, and deterministic budget through normal DB APIs only — never over HTTP
- [x] 2.4 Label the seeded adapter verification as synthetic wherever it surfaces in fixture data or test output
- [x] 2.5 Build the React frontend, then start `uvicorn.Server(...).run()` in a thread on `127.0.0.1:0`; do not use `uvicorn.run()` with reload or workers (D2)
- [x] 2.6 Expose `base_url`, `portal_token`, `task_id`, `entered`, and `release` to the test
- [x] 2.7 Guarantee teardown on success and failure: stop server, undo the monkeypatch, unconditionally set `release`, delete temporary project and database state
- [x] 2.8 Assert seeded content carries no non-DEMO identity or secret, and assert the seeded task body does **not** contain the sentinel string (D5)
- [x] 2.9 Verify with a focused test that the launcher enters and exits cleanly and `GET /health` responds

## 3. Synthetic stream runner

- [x] 3.1 Implement `SyntheticStreamRunner` and patch `foreman_ai_hq.task_launch.streaming_runner` before the server serves; confirm the patch target is the `task_launch` namespace, not `stream_events` (D1)
- [x] 3.2 Emit line 1: a Claude `stream-json` assistant line whose `message.content[]` text carries `DEMO streamed progress 2099`, mapping to an `agent_message` event
- [x] 3.3 Emit line 2: a Claude `result` line with a **top-level** `usage` object, mapping to a `token` event — a shape Claude genuinely emits, so no harness-facing invention is needed (D3)
- [x] 3.4 Keep line 2 free of `session_id`, `modelUsage`, and `total_cost_usd` so it cannot win the first-match race in `parse_native_usage_evidence` (D6)
- [x] 3.5 Set `entered`, block on `stream_more` before emitting the provisional line, then block on `release`, each with a bounded failure timeout; teardown releases every gate unconditionally
- [x] 3.6 After release, emit line 3: a session-bound, model-bound, costed Claude `result` line shaped like `tests/workers/test_adapter_verification.py:398`, with zeroed cache counters, and return the same buffered newline-delimited stdout
- [x] 3.7 Verify at service level after release: task reaches `Review`, `actual_tokens == 15`, and persisted events are `agent_message`, then provisional `token`, then final `token` in that order (Claude maps both `result` lines to token events, unlike OpenCode's trailing `status`)
- [x] 3.8 Verify the final total's evidence provenance is the completion `result` line, not the provisional line — assert `source.type`, `source.session_id`, and the bound model, not only the number (D6)

## 4. Browser scenario

- [x] 4.1 Create `tests/e2e/test_recorded_demo.py` using `playwright.sync_api`
- [x] 4.2 Start `RecordedDemo`, log in through the normal `/login` form, and assert arrival at the React project board route
- [x] 4.3 Launch the seeded task through the normal board control, then wait on `entered` rather than elapsed time
- [x] 4.4 Open the card's `Task details` disclosure, reopening it if a board reload collapses it (D4)
- [x] 4.5 Wait for `DEMO streamed progress 2099` with an explicit timeout of at least 15s; assert the task is still `Running` and the feed offers no reply or acknowledgement affordance
- [x] 4.6 Release `stream_more` only after the board has settled, then assert the token event renders `Provisional usage; final total recorded on completion.` while still `Running`, and assert the incremental `since_id` feed was polled — so the assertion cannot pass off a full board payload
- [x] 4.7 Set `release`; wait for the board to reach `Review` and show final actual token evidence unlabeled as provisional
- [x] 4.8 Open the normal Session Report route and assert the Worker Run timeline shows final evidence with no fabricated provider claim
- [x] 4.9 Invoke the normal Mark Done control and assert `Done`, labeling this in test text as automated synthetic disposition rather than human acceptance
- [x] 4.10 Capture Playwright trace and screenshot on failure only; confirm output is gitignored and nothing is committed

## 5. Documentation and contract updates

- [x] 5.1 Update the `Portal E2E Test` entry in `CONTEXT.md`: scope the `analysis_ready` rule to fixtures that do not substitute a synthetic Worker, and allow a labeled synthetic verified adapter otherwise
- [x] 5.2 Update the `Recorded Demo Run` entry in `CONTEXT.md`: record that the first slice starts from a seeded accepted task, with Markdown intake through accepted estimation deferred to a separate change
- [x] 5.3 Reconcile `docs/PLAYWRIGHT_RECORDED_DEMO_PLAN.md` with anything the implementation changed

## 6. Gates and bookkeeping

- [x] 6.1 Run `uv run pytest -q tests/e2e/test_recorded_demo.py`
- [x] 6.2 Run `uv run pytest -q` and `npm --prefix frontend run check`
- [x] 6.3 Run `openspec validate playwright-recorded-demo --strict --no-interactive`
- [x] 6.4 Settle the open question of whether `tests/e2e/` runs in the default pytest suite or behind a marker or separate CI job, and record the decision
  - Decision: `tests/e2e/` runs in the default pytest suite in this slice. No marker or separate CI job was added. CI must provide a Node toolchain and cached Playwright browsers because `test_recorded_demo.py` builds the React shell and launches Chromium. This is recorded in `docs/PLAYWRIGHT_RECORDED_DEMO_PLAN.md`.
- [x] 6.5 Only after all gates pass: mark `live-worker-run-streaming` tasks 5.6 and 5.7 complete and rerun `openspec validate live-worker-run-streaming --strict --no-interactive`
- [x] 6.6 Request narrow review of `tests/e2e/`, the `pyproject.toml` change, and the `CONTEXT.md` updates
