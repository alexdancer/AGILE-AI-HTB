# AGILE-AI-HTB Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a working vertical-slice AGILE-AI-HTB token-tracker harness from the PRD: FastAPI proxy + SQLite session store + declared guardrails + alarms/checkpoints + minimal portal + synthetic demo fixtures.

**Architecture:** Start with deep, testable domain modules for guardrails, governance decisions, alarms, checkpoints, and persistence. Wrap them with a FastAPI app exposing the OpenAI-compatible proxy endpoint, control-plane APIs, and server-rendered portal. Keep LiteLLM behind an adapter so default tests use fakes and live provider calls remain optional.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, SQLite, PyYAML, LiteLLM, Jinja2, HTMX, Chart.js, pytest.

---

## Milestone 0: Repository foundation

### Task 0.1: Create Python project metadata

**Objective:** Add a minimal installable Python project with app and test dependencies.

**Files:**
- Create: `pyproject.toml`
- Create: `src/agile_ai_htb/__init__.py`
- Create: `tests/__init__.py`

**Implementation notes:**
- Package name: `agile-ai-htb`
- Python requirement: `>=3.11`
- Runtime dependencies: `fastapi`, `uvicorn`, `pydantic`, `pyyaml`, `jinja2`, `python-multipart`, `litellm`
- Test dependencies: `pytest`, `pytest-asyncio`, `httpx`
- Configure pytest to use `tests/` and add `src/` to import path.

**Verification:**
- Run: `python -m pip install -e '.[test]'`
- Run: `python -m pytest -q`
- Expected: test discovery succeeds; zero tests or initial placeholder tests pass.

### Task 0.2: Add application settings module

**Objective:** Centralize filesystem paths and runtime settings.

**Files:**
- Create: `src/agile_ai_htb/settings.py`
- Test: `tests/test_settings.py`

**Behavior:**
- `Settings` has `database_path`, `guardrails_path`, `timezone`, and `provider_api_key_env` fields.
- Defaults point to local development values: `harness.db`, `guardrails.yaml`, local timezone, provider API key environment variable name.
- Environment variables can override paths.

**Verification:**
- Run: `python -m pytest tests/test_settings.py -q`
- Expected: defaults and env overrides pass.

---

## Milestone 1: Guardrail configuration and governance decisions

### Task 1.1: Parse guardrail YAML

**Objective:** Load `guardrails.yaml` into typed objects.

**Files:**
- Create: `src/agile_ai_htb/guardrails.py`
- Test: `tests/test_guardrails.py`
- Read fixture: `guardrails.yaml`

**Behavior:**
- `load_guardrails(path) -> GuardrailConfig`
- Preserve configured thresholds, max tokens, blocked tools, loop threshold, timeout, tool category limits, notifications, and model routing.
- Validate zone ordering: `green < yellow <= red`.

**Verification:**
- Run: `python -m pytest tests/test_guardrails.py -q`
- Expected: real repo `guardrails.yaml` parses and exposes expected values.

### Task 1.2: Implement budget zone calculation

**Objective:** Calculate green/yellow/red zone from live daily usage and daily cap.

**Files:**
- Modify: `src/agile_ai_htb/guardrails.py`
- Test: `tests/test_guardrails.py`

**Behavior:**
- `get_budget_zone(used_tokens, daily_cap, config) -> Literal['green','yellow','red']`
- Green is below configured green threshold.
- Yellow is at or above green threshold and below red threshold.
- Red is at or above configured yellow threshold.
- Zero or missing cap remains green and does not divide by zero.

**Verification:**
- Run: `python -m pytest tests/test_guardrails.py -q`
- Expected: boundary tests pass at 0%, 59.9%, 60%, 84.9%, 85%, and over 100%.

### Task 1.3: Implement request governance transform

**Objective:** Apply three-layer graduated enforcement to an OpenAI-compatible request body.

**Files:**
- Create: `src/agile_ai_htb/governance.py`
- Test: `tests/test_governance.py`

**Behavior:**
- `apply_governance(request: dict, zone: str, config: GuardrailConfig) -> GovernanceDecision`
- Prepends or replaces a system message with the configured zone prompt.
- Clamps `max_tokens` to the configured zone maximum, never increasing a smaller caller-provided value.
- Removes blocked tools by function/tool name for yellow and red zones.
- Returns both the transformed request and a decision summary containing zone, blocked tools, and max token clamp.

**Verification:**
- Run: `python -m pytest tests/test_governance.py -q`
- Expected: green leaves tools intact; yellow removes exploratory tools; red keeps only delivery-safe tools according to config.

---

## Milestone 2: SQLite persistence and session artifacts

### Task 2.1: Create SQLite schema and database initializer

**Objective:** Persist sessions, tasks, token turns, tool traces, alarms, snapshots, checkpoints, and action history.

**Files:**
- Create: `src/agile_ai_htb/db.py`
- Test: `tests/test_db.py`

**Behavior:**
- `init_db(path)` creates all tables idempotently.
- Tables include timestamps and JSON text columns for flexible artifact payloads.
- Foreign keys are enabled.

**Verification:**
- Run: `python -m pytest tests/test_db.py -q`
- Expected: schema initializes twice without error and expected tables exist.

### Task 2.2: Implement repository functions

**Objective:** Provide a small persistence API for the app and domain modules.

**Files:**
- Modify: `src/agile_ai_htb/db.py`
- Test: `tests/test_db.py`

**Behavior:**
- Create/get session with task description, model, session key hash/reference, started timestamp, status, and guardrail overrides JSON.
- Record token turn with model, prompt tokens, completion tokens, total tokens, cost, and raw usage JSON.
- Record guardrail snapshot with zone and governance decision JSON.
- Record alarms and checkpoint results.
- Build a session artifact dictionary from persisted rows.

**Verification:**
- Run: `python -m pytest tests/test_db.py -q`
- Expected: create session, record rows, and rebuild artifact all work against temporary SQLite.

---

## Milestone 3: Alarms and checkpoints

### Task 3.1: Implement alarm generation

**Objective:** Convert guardrail deviations into structured alarm objects.

**Files:**
- Create: `src/agile_ai_htb/alarms.py`
- Test: `tests/test_alarms.py`

**Behavior:**
- Stable alarm types: `BUDGET_YELLOW`, `BUDGET_RED`, `DAILY_CAP_EXCEEDED`, `SESSION_CAP_EXCEEDED`, `LOOP_DETECTED`, `SESSION_TIMEOUT`, `TOOL_CATEGORY_BIAS`, `CHECKPOINT_FAIL`.
- Alarm object includes id, type, severity, session_id, timestamp, context, recommended_action.
- Budget zone alarms fire once per session per zone transition.
- Daily/session cap alarms fire when totals cross caps.

**Verification:**
- Run: `python -m pytest tests/test_alarms.py -q`
- Expected: each alarm has correct severity and context; duplicate zone alarms are suppressed.

### Task 3.2: Implement loop detection

**Objective:** Detect repeated identical tool calls.

**Files:**
- Modify: `src/agile_ai_htb/alarms.py`
- Test: `tests/test_alarms.py`

**Behavior:**
- `detect_loop(tool_trace, threshold) -> Alarm | None`
- Consecutive identical `(tool_name, input_hash)` calls at threshold produce `LOOP_DETECTED`.
- Non-consecutive repetition does not trigger unless it becomes consecutive again.

**Verification:**
- Run: `python -m pytest tests/test_alarms.py::test_loop_detection -q`
- Expected: threshold behavior passes.

### Task 3.3: Implement checkpoint evaluator

**Objective:** Evaluate persisted artifacts at session boundaries.

**Files:**
- Create: `src/agile_ai_htb/checkpoints.py`
- Test: `tests/test_checkpoints.py`

**Behavior:**
- `evaluate_checkpoints(artifact, config) -> list[CheckpointResult]`
- Budget health compares session spend to configured session cap or a fair-share heuristic.
- Stuck-loop score fails if loop alarm count is 3 or more.
- Tool diversity passes if at least 3 distinct categories appear, unless red-zone restrictions explain a review condition.
- Timeout respect fails if a timeout alarm exists.

**Verification:**
- Run: `python -m pytest tests/test_checkpoints.py -q`
- Expected: pass/fail cases are deterministic from artifact dictionaries.

---

## Milestone 4: Control-plane API

### Task 4.1: Create FastAPI app factory

**Objective:** Wire settings, database, guardrails, templates, and route modules.

**Files:**
- Create: `src/agile_ai_htb/app.py`
- Create: `src/agile_ai_htb/routes/__init__.py`
- Test: `tests/test_app.py`

**Behavior:**
- `create_app(settings: Settings | None = None) -> FastAPI`
- Startup initializes SQLite and loads guardrails.
- Health endpoint `GET /health` returns status.

**Verification:**
- Run: `python -m pytest tests/test_app.py -q`
- Expected: health endpoint returns 200 with `{"status":"ok"}`.

### Task 4.2: Add session API

**Objective:** Support session creation and reporting.

**Files:**
- Create: `src/agile_ai_htb/routes/sessions.py`
- Modify: `src/agile_ai_htb/app.py`
- Test: `tests/test_sessions_api.py`

**Behavior:**
- `POST /session/start` accepts task description, model, optional budget, optional guardrail overrides.
- Returns session id, session-scoped API key, starting zone, and report URL.
- `GET /session/{id}/report` returns token totals, current zone, alarms, checkpoints, tool breakdown placeholder, and task metadata.
- `GET /session/{id}/artifact` returns raw artifact.
- `POST /session/{id}/checkpoint/evaluate` stores and returns checkpoint results.

**Verification:**
- Run: `python -m pytest tests/test_sessions_api.py -q`
- Expected: session lifecycle works against temporary DB.

### Task 4.3: Add task and estimation API

**Objective:** Populate the AGILE board and produce simple deterministic estimates.

**Files:**
- Create: `src/agile_ai_htb/routes/tasks.py`
- Create: `src/agile_ai_htb/estimation.py`
- Modify: `src/agile_ai_htb/app.py`
- Test: `tests/test_tasks_api.py`

**Behavior:**
- `POST /tasks` creates a task in Backlog.
- `PUT /tasks/{id}` updates status, estimate, model, or description.
- `POST /estimate` returns token estimate, complexity, recommended model, optional budget-aware downgrade note.
- Initial estimator can be deterministic heuristics based on keywords and description length; no paid model call in default path.

**Verification:**
- Run: `python -m pytest tests/test_tasks_api.py -q`
- Expected: estimates classify easy/modest/complex demo tasks and apply budget-aware downgrade.

### Task 4.4: Add alarm action API

**Objective:** Let humans respond to alarms through the control plane.

**Files:**
- Create: `src/agile_ai_htb/routes/alarms.py`
- Modify: `src/agile_ai_htb/app.py`
- Test: `tests/test_alarms_api.py`

**Behavior:**
- `GET /alarms` lists alarms with filters by session, type, severity, and resolved state.
- `POST /alarms/{id}/resolve` records action: continue, abort_session, raise_budget, or adjust_guardrail.
- Actions update persisted state where applicable, but never silently discard the alarm history.

**Verification:**
- Run: `python -m pytest tests/test_alarms_api.py -q`
- Expected: alarms can be listed and resolved with action history.

---

## Milestone 5: LiteLLM proxy data plane

### Task 5.1: Create LiteLLM adapter

**Objective:** Isolate provider forwarding and usage extraction.

**Files:**
- Create: `src/agile_ai_htb/llm.py`
- Test: `tests/test_llm_adapter.py`

**Behavior:**
- `LLMClient.acompletion(request: dict)` calls `litellm.acompletion(**request)`.
- `extract_usage(response)` returns prompt tokens, completion tokens, total tokens.
- `calculate_cost(model, prompt_tokens, completion_tokens)` wraps LiteLLM cost calculation and safely returns `0` or `None` when pricing is unavailable.
- Streaming helper reads usage from the final usage chunk only.

**Verification:**
- Run: `python -m pytest tests/test_llm_adapter.py -q`
- Expected: fake responses and fake streaming chunks produce correct usage.

### Task 5.2: Implement `/v1/chat/completions` non-streaming path

**Objective:** Govern a request, forward it, persist usage, and return provider response.

**Files:**
- Create: `src/agile_ai_htb/routes/proxy.py`
- Modify: `src/agile_ai_htb/app.py`
- Test: `tests/test_proxy_api.py`

**Behavior:**
- Auth header bearer token maps to a session key.
- Current daily usage determines zone before forwarding.
- Governance transform is applied before calling the LLM adapter.
- Usage and guardrail snapshot are persisted after response.
- Budget alarms are generated and persisted after token recording.
- Response remains OpenAI-compatible.

**Verification:**
- Run: `python -m pytest tests/test_proxy_api.py -q`
- Expected: fake LLM receives transformed request; DB contains token turn, snapshot, and alarms.

### Task 5.3: Implement streaming proxy path

**Objective:** Support `stream: true` while preserving accurate final usage accounting.

**Files:**
- Modify: `src/agile_ai_htb/routes/proxy.py`
- Modify: `src/agile_ai_htb/llm.py`
- Test: `tests/test_proxy_streaming.py`

**Behavior:**
- Pass through streaming chunks to the caller.
- Request `stream_options={"include_usage": True}` when streaming.
- Do not sum intermediate chunk usage.
- Persist usage only from the final usage chunk.
- Persist a guardrail snapshot for the request.

**Verification:**
- Run: `python -m pytest tests/test_proxy_streaming.py -q`
- Expected: streamed chunks reach client and final persisted usage equals final chunk usage only.

---

## Milestone 6: Portal vertical slice

### Task 6.1: Add base templates and dashboard route

**Objective:** Render a usable dashboard without a frontend build step.

**Files:**
- Create: `src/agile_ai_htb/routes/portal.py`
- Create: `src/agile_ai_htb/templates/base.html`
- Create: `src/agile_ai_htb/templates/dashboard.html`
- Modify: `src/agile_ai_htb/app.py`
- Test: `tests/test_portal.py`

**Behavior:**
- `GET /dashboard` renders global daily budget usage, session count, alarm count, and links to task board/session history.
- Include HTMX and Chart.js via CDN script tags.
- No secrets or provider keys appear in HTML.

**Verification:**
- Run: `python -m pytest tests/test_portal.py -q`
- Expected: dashboard returns 200 HTML containing budget and alarm sections.

### Task 6.2: Add AGILE board view

**Objective:** Show tasks and session lifecycle in portal form.

**Files:**
- Create: `src/agile_ai_htb/templates/board.html`
- Modify: `src/agile_ai_htb/routes/portal.py`
- Test: `tests/test_portal.py`

**Behavior:**
- `GET /board` renders columns Backlog, Estimated, Running, Review, Done.
- Each task card shows description, estimate, recommended model, actual token cost if available, and session link if available.
- Board uses server-rendered HTML; HTMX actions can be progressive enhancements.

**Verification:**
- Run: `python -m pytest tests/test_portal.py::test_board_renders_columns -q`
- Expected: all board columns render.

### Task 6.3: Add session report view

**Objective:** Render per-session audit details.

**Files:**
- Create: `src/agile_ai_htb/templates/session_report.html`
- Modify: `src/agile_ai_htb/routes/portal.py`
- Test: `tests/test_portal.py`

**Behavior:**
- `GET /sessions/{id}` renders token totals, zone timeline, alarms, checkpoint results, and raw artifact link.
- Alarmed/checkpoint-failed sessions visibly require review.

**Verification:**
- Run: `python -m pytest tests/test_portal.py::test_session_report_renders -q`
- Expected: report HTML contains totals and alarm/checkpoint sections.

---

## Milestone 7: Demo fixtures and synthetic project

### Task 7.1: Create synthetic `snip` scaffold

**Objective:** Add the demo project starting state described in `docs/DEMO.md`.

**Files:**
- Create: `demo/snip/pyproject.toml`
- Create: `demo/snip/src/snip/__init__.py`
- Create: `demo/snip/src/snip/cli.py`
- Create: `demo/snip/src/snip/store.py`
- Create: `demo/snip/tests/test_scaffold.py`

**Behavior:**
- CLI parser exists with command names but commands intentionally return not-implemented messages.
- Store has constructor but no persistence methods yet.
- The scaffold is small and safe for live agent tasks.

**Verification:**
- Run: `cd demo/snip && python -m pytest -q`
- Expected: scaffold tests pass and confirm command placeholders.

### Task 7.2: Seed demo tasks in harness

**Objective:** Provide the six demo board tasks from `docs/DEMO.md`.

**Files:**
- Create: `src/agile_ai_htb/demo_seed.py`
- Test: `tests/test_demo_seed.py`

**Behavior:**
- `seed_demo_tasks(db_path)` inserts T1-T6 if they do not already exist.
- Seeded tasks include description, complexity, estimate, and recommended model.
- Function is idempotent.

**Verification:**
- Run: `python -m pytest tests/test_demo_seed.py -q`
- Expected: six tasks inserted once.

### Task 7.3: Add fake-data invariant tests

**Objective:** Prove demo artifacts contain only obviously synthetic values.

**Files:**
- Create: `tests/test_demo_fake_data_invariants.py`

**Behavior:**
- Test class name: `TokenTrackerHarnessDemoFakeDataInvariantTests`.
- Scans demo files for obvious live credential markers and real-looking API tokens.
- Requires demo text or generated demo records to be clearly synthetic where applicable.
- Ensures no `.env` files or real secrets are introduced under `demo/`.

**Verification:**
- Run: `python -m pytest tests/test_demo_fake_data_invariants.py -q`
- Expected: fake-data invariant tests pass.

---

## Milestone 8: Local run, Docker, and docs

### Task 8.1: Add local CLI entrypoint

**Objective:** Make the harness easy to start locally.

**Files:**
- Create: `src/agile_ai_htb/__main__.py`
- Modify: `pyproject.toml`
- Test: `tests/test_cli_entrypoint.py`

**Behavior:**
- Console script `htb` is the AGILE-AI-HTB operator command.
- Python package distribution is `agile-ai-htb`; Python import package is `agile_ai_htb`.
- CLI is an operator entrypoint only; task/session/alarm workflows remain portal/API-first. No CRUD CLI is added for Milestone 8.
- Bare `htb` defaults to `htb serve`.
- `htb serve` starts uvicorn with `agile_ai_htb.app:create_app` using factory mode.
- `htb serve` supports host, port, database path, and guardrails path arguments; CLI arguments override environment defaults.
- `htb seed-demo` inserts the synthetic DEMO snip tasks into the harness database.

**Verification:**
- Run: `htb --help`
- Run: `htb serve --help`
- Run: `htb seed-demo --help`
- Run: `python -m pytest tests/test_cli_entrypoint.py -q`
- Expected: help prints and CLI tests pass.

### Task 8.2: Add Docker and compose files

**Objective:** Package the single-process app for demo startup.

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Behavior:**
- Container installs the package and runs the harness on port 8000.
- SQLite database is persisted in a mounted volume.
- `guardrails.yaml` is mounted/readable in the container.

**Verification:**
- Run: `docker compose build`
- Run: `docker compose up -d`
- Run: `curl -fsS http://localhost:8000/health`
- Run: `docker compose down`
- Expected: health endpoint returns OK.

### Task 8.3: Add operator README

**Objective:** Document setup, run, demo, and verification commands.

**Files:**
- Create: `README.md`

**Behavior:**
- Includes local install command, test command, Docker command, portal URL, `htb seed-demo` command, and optional live LiteLLM smoke test instructions.
- Clearly states that provider keys belong in environment variables and are not stored in repo.

**Verification:**
- Run commands from README where possible: install, tests, local health check.
- Expected: documented default path works without provider API keys.

---

## Milestone 9: End-to-end vertical slice verification

### Task 9.1: Add full local integration test

**Objective:** Prove the core PRD workflow works without paid provider calls.

**Files:**
- Create: `tests/test_vertical_slice.py`

**Behavior:**
- Start app with temp SQLite and real `guardrails.yaml`.
- Create a task.
- Estimate the task.
- Start a session.
- Send fake-authenticated `/v1/chat/completions` request using fake LLM adapter.
- Verify transformed request, persisted usage, alarm behavior, report payload, and dashboard HTML.

**Verification:**
- Run: `python -m pytest tests/test_vertical_slice.py -q`
- Expected: complete vertical slice passes.

### Task 9.2: Run project quality gate

**Objective:** Verify the implementation is ready for demo iteration.

**Files:**
- No new files.

**Verification:**
- Run: `python -m pytest -q`
- Run: `python -m compileall src tests`
- Run: `git status --short`
- Expected: tests pass, compile succeeds, and changed files are reviewable.

---

## Implementation order and stopping points

1. Complete Milestones 0-3 first. This proves the core harness rules independently of any web UI.
2. Complete Milestones 4-5 next. This proves the real proxy/control-plane vertical slice.
3. Complete Milestone 6. This makes the demo visible.
4. Complete Milestone 7. This gives the challenge a safe synthetic demo surface.
5. Complete Milestones 8-9. This packages and verifies the full local artifact.

After each milestone, run its targeted tests plus `python -m pytest -q` if the suite remains fast. Do not call real LLM providers in default tests. Use fake adapters for deterministic behavior and reserve live LiteLLM verification for an explicit manual smoke command.
