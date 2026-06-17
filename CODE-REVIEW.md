# AGILE-AI-HTB — Comprehensive Code Review

**Date:** 2026-06-16  
**Commit:** `79de338` — `feat: separate control-plane and Worker Harness models`  
**Tests:** 244 passed, 0 failed, 2 warnings (4.40s)  
**Language:** Python 3.11 · FastAPI · SQLite · LiteLLM · Jinja2  
**Lines:** ~25 source files · ~9,000 LOC Python · ~500 LOC HTML templates · ~500 LOC YAML config

---

## 1. Architecture Overview

AGILE-AI-HTB is a **portal-first token-budget governance harness** for AI coding agents. It wraps worker CLIs (OpenCode, Claude Code, Codex, Hermes) with transport-level guardrails, tracks token spend by category, and escalates budget violations to a human operator — never to the agent itself.

### Two Model Layers
- **Control Plane** — the portal's own LLM for task estimation, reporting. Uses a single model (`gpt-4o-mini` by default) via LiteLLM.
- **Worker Harness** — the coding agent CLI. Models are discovered from each adapter natively (`opencode models` for OpenCode; no `--json` flag). Two tracking modes:
  - **Proxy-governed**: Worker routes LLM calls through the harness proxy (`/v1/chat/completions`). The proxy records usage, applies governance transforms, and fires alarms.
  - **Native usage**: Worker uses its own auth/config. Usage evidence is parsed from stdout (JSON with `usage` objects matching the launched model).

### Four Pillars (Design Intent)
| Pillar | Implementation |
|--------|---------------|
| **Guardrails** | 6 constraints defined in `guardrails.yaml`. Enforced at proxy level and at task launch. |
| **Checkpoints** | 4 stateless evaluators: budget_health, stuck_loop_score, tool_diversity, timeout_respect |
| **Material Handling** | Kanban board (6 columns), dashboard, session reports, REST + HTML dual delivery |
| **Alarms** | 7 types + CHECKPOINT_FAIL. Each carries severity + recommended action. Operator resolves via UI. |

---

## 2. Module-by-Module Implementation Status

### `app.py` — App factory
**Status: Complete, working.**

- FastAPI lifespan: inits DB, loads guardrails, creates LLM client, optionally boots LocalExecutionBackend.
- `_bridge_provider_key()` copies the control-plane API key to provider-specific env vars so LiteLLM can find it. This is a **pragmatic workaround** for LiteLLM's env-var-based auth — but it copies the key to *all* providers (Anthropic, OpenAI, Cohere, Groq) regardless of which is actually used. Low risk in single-provider deployments.

### `settings.py` — Configuration
**Status: Complete, working. Awkward implementation.**

- Frozen dataclass with `object.__setattr__` for env-var overrides. Works, but the `__init__` override is unusual.
- `estimator_model` is always set equal to `control_plane_model` — making it a redundant field.
- Multiple env-var fallbacks (`AGILE_AI_HTB_CONTROL_API_KEY_ENV`, `TOKEN_TRACKER_CONTROL_PLANE_API_KEY_ENV`, then hardcoded default). The fallback chain is thorough but complex.

### `db.py` — SQLite persistence
**Status: Complete, working. Minor concerns.**

- 9 tables: sessions, tasks, token_turns, tool_traces, alarms, guardrail_snapshots, checkpoint_results, action_history, worker_adapters, connected_projects, execution_backend_status.
- Migration is ad-hoc: checks `pragma table_info` for column/table existence. No migration versioning table. Works for current scope, fragile for production schema evolution.
- No WAL mode enabled. SQLite in default rollback-journal mode serializes writers. Under concurrent proxy requests this could cause `database is locked` errors under load.
- `_classified_raw_usage()` and `_spend_category_for_usage_kind()` provide spend categorization (control_plane, worker_execution, adapter_verification, reporting_summary). Well-structured.
- `token_usage_breakdown()` returns by-category and by-source breakdowns. Used by dashboard and budget evaluation.

### `auth.py` — Portal authentication
**Status: Complete, working.**

- HMAC-signed cookie auth + Bearer token support.
- Cookie max age 12 hours by default.
- Uses `secrets.compare_digest()` correctly for timing-safe comparison.
- No session tracking — cookie is stateless (verified against env var). Simple and secure for single-operator use.

### `llm.py` — LiteLLM wrapper
**Status: Complete, working. Thin.**

- `LLMClient.acompletion()` is a straight passthrough to `litellm.acompletion(**request)`.
- `extract_usage()` handles dict and object responses via `_get()` helper.
- `calculate_cost()` silently returns `None` on LiteLLM cost-calculation failure — callers handle this, but `None` cost flows into `record_token_turn()` which stores `cost or 0.0`. Acceptable.
- `final_stream_usage()` is defined but **never called** from the proxy route. The proxy (`routes/proxy.py:64-79`) does its own streaming logic. Dead code.

### `guardrails.py` — Config loader + zone math
**Status: Complete, working.**

- Parses `guardrails.yaml` into frozen dataclasses.
- Validates zone thresholds: `green < yellow <= red`.
- `get_budget_zone()` returns green/yellow/red based on usage ratio.
- Well-structured, single-purpose module.

### `governance.py` — Transport-level enforcement
**Status: Complete, working.**

- Three-layer enforcement per zone:
  1. **System prompt rewrite** — replaces/inserts zone-specific prompt
  2. **max_tokens clamping** — `min(requested, zone_max)`
  3. **Tool filtering** — removes blocked tools; red zone additionally allowlists only read/patch/terminal
- `deepcopy`s the request before mutation — important for non-destructive transforms.
- The `RED_ALLOWED_TOOL_NAMES` constant is hardcoded. Would benefit from being config-driven.

### `alarms.py` — Alarm detection
**Status: Complete, working.**

- 7 alarm types: BUDGET_YELLOW, BUDGET_RED, DAILY_CAP_EXCEEDED, SESSION_CAP_EXCEEDED, LOOP_DETECTED, SESSION_TIMEOUT, TOOL_CATEGORY_BIAS.
- `detect_budget_alarms()` is idempotent — checks `previous_alarms` to avoid duplicate firings.
- `detect_loop()` tracks consecutive identical (tool_name, input_hash) pairs.
- All alarms carry severity + recommended action text.
- `CHECKPOINT_FAIL` alarm is generated separately in `checkpoints.py`.

### `checkpoints.py` — Session boundary evaluations
**Status: Complete, working.**

- 4 stateless evaluators: budget_health, stuck_loop_score, tool_diversity, timeout_respect.
- Each operates on a session artifact dict — replayable from DB.
- `_tool_diversity()` special-cases red-zone restrictions as a valid reason for low diversity.
- Hardcoded tool-to-category mapping (file_io, shell, web, vision, code_exec, delegation).

### `estimation.py` — Task token estimation
**Status: Complete, working. Most complex validation.**

- Sends task description to control-plane LLM with `response_format: json_object`.
- Validates response exhaustively: required fields, types, ranges, allowed values.
- 8 named `EstimatorError` subclasses for different failure modes.
- `_validate_result()` is ~60 lines of field-by-field validation. Thorough but verbose.
- Bare `isinstance(confidence, int | float)` on Python 3.11 — this is correct for 3.11+ `isinstance` union support.

### `execution_backend.py` — Local Runner
**Status: Complete, working.**

- `LocalExecutionBackend` connects local projects via `connect_project()`.
- Detects project profile: language hints, framework hints, test/run commands, top-level structure.
- `build_project_capability()` returns state: `launch_ready`, `analysis_ready`, or `blocked`.
- `create_read_only_proof_task()` creates a pre-built read-only verification task for OpenCode.
- Hardcodes `opencode` adapter in `_configure_local_opencode_adapter()` — would need change for other adapters.

### `task_launch.py` — Task → session orchestration
**Status: Complete, working. Most complex orchestration.**

- `launch_task()` is ~340 lines, the largest function in the codebase. Handles:
  - Status validation (Estimated/Ready only, unless manual estimate override)
  - Adapter selection (default or explicit)
  - Budget evaluation (worker_execution spend vs daily cap)
  - Launch guardrails (adapter verification, model support, tracking mode)
  - Session creation
  - Subprocess execution via `CommandPlan`
  - Native usage parsing
  - Read-only diff detection (git porcelain before/after)
  - Write-capable: branch creation, test verification, git commit
  - Budget overrun alarming
- `_run_test_command()` uses `shell=True` with the detected test command string. The command comes from project detection, not user input, so the risk is low — but `shell=True` is still a **code smell** and should be `shell=False` with `shlex.split()`.

### `launch_guardrails.py` — Pre-launch validation
**Status: Complete, working.**

- `evaluate_launch_guardrails()` checks: adapter existence, configuration, verification status, tracking mode, workdir existence, model support, proxy URL readiness.
- `adapter_launchable_for_ui()` is a UI convenience that mirrors the guardrail logic for display purposes.

### `worker_adapters.py` — Adapter subsystem
**Status: Complete, working. Most innovative part.**

- 4 adapters: Claude Code, Codex, OpenCode, Hermes. Each has:
  - `verification_template` — command to verify adapter works
  - `launch_template` — command to launch a task
  - `native_verification_template` / `native_launch_template` — for native usage mode
  - `model_discovery_template` — command to list available models
- `WorkerAdapterBuilder` builds `CommandPlan` objects with command, cwd, env, metadata.
- `verify_worker_adapter()` creates a verification session, runs the adapter with `SENTINEL_PROMPT`, and checks for exact `AGILE_AI_HTB_ADAPTER_OK` response.
- Native usage mode: parses stdout for JSON usage evidence via `_parse_native_usage_evidence()`.
- `_parse_native_usage_evidence()` is remarkably thorough — walks JSON trees, handles 6 different token field names, handles "$" prefix in costs, "K" suffix in token counts.
- `_redact_command()` handles `--api-key`, `--token`, `-H "Authorization:"` patterns for secret safety.
- `subprocess_runner()` has good error handling: TimeoutExpired → returncode 124, OSError → returncode 127.

### `routes/proxy.py` — Harness proxy (LiteLLM-compatible)
**Status: Complete, working.**

- Exposes `/v1/chat/completions` — OpenAI-compatible endpoint.
- Authenticates via session bearer token (hashed).
- Applies governance transforms before forwarding to LiteLLM.
- Handles both streaming and non-streaming responses.
- Persists token turns and budget alarms after each completion.
- Streams use `stream_options: {include_usage: true}` to get final usage from last chunk.

### `routes/tasks.py` — Task CRUD + estimation + launch
**Status: Complete, working.**

- Full task lifecycle: create, update, estimate, launch, refresh.
- `_initial_task_status_and_metadata()` enforces that tasks must be Estimated before Ready, and Ready before launch.
- `_constrain_direct_lifecycle_status()` blocks direct transitions to Running (must use launch endpoint) and Done/Review (must use refresh endpoint).
- `_constrained_recommended_model()` restricts estimator recommendations to Worker-adapter-discovered models.
- Estimation failures gracefully create Blocked tasks with `requires_manual_estimate: true`.

### `routes/portal.py` — HTML portal
**Status: Complete, working.**

- Full set of HTML pages: login, dashboard, board, sessions, session report, workers, control-plane, project.
- Dual content-type handling (JSON API + HTML forms) via `_worker_verify_payload_from_request()` and `_launch_payload_from_request()`.
- `WorkerVerifyRequest` and `ProjectConnectRequest` use Pydantic validation with regex patterns.
- Dashboard shows KPIs: daily budget progress bar, active sessions, open alarms, token breakdown.
- Board view groups tasks by the 6 canonical columns.

### `routes/sessions.py` — Session API
**Status: Complete, working.**

- `/session/start` — creates a session manually (for non-task-driven use).
- `/session/{id}/report` — lightweight JSON report.
- `/session/{id}/artifact` — full session artifact (portal-authenticated).
- `/session/{id}/checkpoint/evaluate` — runs stateless checkpoint evaluations.

### `routes/alarms.py` — Alarm listing + resolution
**Status: Complete, working.**

- Lists alarms with optional filtering (session_id, type, severity, resolved).
- HTML view separates open/resolved, counts critical/warning.
- `/alarms/{id}/resolve` supports 4 actions: continue, abort_session, raise_budget, adjust_guardrail.
- Actions are persisted in `action_history` table with applied side effects.

### Templates — Jinja2 HTML
**Status: Complete, working.**

- `base.html` — shared layout with navigation (Dashboard, Board, Sessions, Alarms, Workers, Control Plane, Project).
- `login.html` — simple token form.
- `dashboard.html` — KPI grid + active sessions table.
- `board.html` — Kanban board with 6 columns, task cards.
- `sessions.html` — session list with zone indicators.
- `session_report.html` — detailed session artifact view.
- `alarms.html` — open/resolved alarm lists with resolve forms.
- `workers.html` — adapter configuration + verification + model discovery.
- `control_plane.html` — control-plane model settings and connection test.
- `project.html` — project connection + read-only proof launch.
- `alarm_card.html` — reusable alarm card component.

### `cli.py` — Operator CLI
**Status: Complete, working.**

- Two commands: `htb serve` (start portal server) and `htb seed-demo` (seed synthetic tasks).
- `--local-runner` flag enables the Local Runner execution backend.

---

## 3. Test Coverage

**244 tests passing** across ~20 test files.

### Test categories:
- **Unit tests**: settings, guardrails, zone math, session lifecycle
- **Integration tests**: FastAPI routes via TestClient, DB operations
- **Behavioral evals**: 31 tests across `test_eval_*` files:
  - `test_eval_alarm_firing.py` — verifies alarm detection logic
  - `test_eval_estimator.py` — verifies estimation validation
  - `test_eval_proxy_token_tracking.py` — verifies proxy-governed token recording
  - `test_eval_zone_transitions.py` — verifies zone transition behavior
- **Demo invariant tests**: `test_mockup_fixtures.py` — verifies all demo data is synthetic
- **Project setup tests**: `test_project_setup.py` — Local Runner connection + read-only proof
- **Worker adapter tests**: verification, model discovery, secret redaction

**All tests use fake LLM clients. Zero provider calls. Zero cost.**

---

## 4. Problems & Issues Found

### 🔴 High Priority

1. **`shell=True` in `_run_test_command()`** (`task_launch.py:687`)  
   The test command string is passed to `subprocess.run(command, shell=True, ...)`. While the command originates from project detection (not direct user input), it's still an injection surface. Should use `shlex.split(command)` with `shell=False`.

2. **No WAL mode in SQLite** (`db.py:161-165`)  
   Multiple concurrent proxy requests will serialize on writes. A single `pragma journal_mode=wal` in `init_db()` would fix this.

### 🟡 Medium Priority

3. **Duplicate utility functions across routes**  
   `_daily_cap_tokens()`, `_token_totals()` are copied in `routes/proxy.py`, `routes/sessions.py`, and `routes/portal.py`. Should be factored into a shared module.

4. **Dead code — `final_stream_usage()`** (`llm.py:39-45`)  
   Defined but never called. The proxy does its own streaming accumulation. Remove or use.

5. **README says "197 tests" — actual count is 244**  
   Stale documentation. Test count and file list need updating.

6. **Hardcoded model names in multiple places**  
   `guardrails.yaml` has old Anthropic model names (`claude-3-5-sonnet-20240620`, `claude-3-opus-20240229`). `db.py:WORKER_ADAPTER_PRESETS` has model lists. `settings.py` defaults to `gpt-4o-mini`. These will go stale and cause real LLM call failures. The recent commit `5a22f0a` (fix: replace invalid LiteLLM model names) shows this is a recurring problem.

7. **`_bridge_provider_key()` copies key to all providers** (`app.py:33-44`)  
   The control-plane API key is set as both `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` etc. If someone uses a provider-specific key, it could conflict. Should only set the key for the actual provider being used.

### 🟢 Low Priority

8. **No migration versioning** (`db.py:176-239`)  
   Ad-hoc migrations work but are fragile. A simple `schema_version` table would prevent drift.

9. **`estimator_model` is redundant** (`settings.py:81-85`)  
   Always set to the same value as `control_plane_model`. Either remove the field or document the distinction.

10. **No rate limiting** on portal API or proxy endpoints. A runaway worker could hammer the proxy.

11. **No structured logging** — all output is `print()` or uvicorn defaults. Makes production debugging harder.

12. **No observability/metrics** beyond what's in the DB tables. No Prometheus endpoints, no tracing.

13. **`WORKER_ADAPTER_PRESETS` is static** (`db.py:129-158`)  
    New adapter versions will require code changes. Would benefit from a config-file-based adapter registry.

14. **No graceful shutdown for running worker sessions** — if the harness restarts, running subprocesses are orphaned.

15. **`settings.py` uses `object.__setattr__` on a frozen dataclass** — works but is a code smell. A plain `__init__`-based class would be cleaner.

---

## 5. Design Observations

### What's Good
- **Clean separation of concerns**: Guardrails → Governance → Alarms → Checkpoints are independent layers. Each can be tested in isolation.
- **Human-in-the-loop enforcement**: Alarms recommend actions but never auto-kill sessions (except by operator choice).
- **Dual-mode tracking**: Proxy-governed for generic OpenAI-compatible agents; native usage for CLI-specific tools. Good flexibility.
- **Exhaustive validation in estimation**: Every field is validated for type, range, and allowed values. Defensive.
- **Secret redaction is thorough**: Command plans, env vars, stdout, and DB evidence are all redacted before persistence.
- **Test suite is fast and isolated**: All 244 tests run in 4.4s with zero external calls. Fake LLM clients throughout.
- **Docker deployment is straightforward**: Single `Dockerfile`, well-documented env vars.
- **The HTML portal is functional and complete**: Every page serves both API and HTML consumers.

### What's Missing
- **No adapter auto-detection on startup** — the OpenCode adapter's workdir must be manually configured or set via project connection. When OpenCode is installed, it should be auto-discovered.
- **No agent-to-portal push** — the proxy is pull-only. A real worker could report tool traces, checkpoints, or alarms back without going through the proxy.
- **No multi-user/multi-tenant support** — single operator, single portal token. Fine for v0.1 but limits scale.
- **No budget rollover or multi-day tracking** — daily caps reset at midnight. No weekly/monthly aggregates.
- **No webhook notifications** — the config has `discord_webhook` and `slack_webhook` fields but no code calls them.
- **No session resumption** — if a worker fails, there's no way to continue an in-progress session with accumulated context.

### Architecture Decision: SQLite
SQLite is the right choice for this scope. It's zero-config, portable, and the schema is simple. Migrating to Postgres would only be warranted when multi-instance deployment is needed. The current WAL-mode gap is the only immediate concern.

### Architecture Decision: Jinja2 Server-Side Rendering
The choice of server-side templates (no SPA, no npm) is consistent with the user's stated preference for simplicity. The templates are clean HTML with inline CSS — no build step needed.

---

## 6. Immediate Recommendations (in priority order)

1. **Fix `shell=True` in `_run_test_command()`** — use `shlex.split()` + `shell=False`
2. **Enable WAL mode in SQLite** — one-line change in `init_db()`
3. **Update README test count and model names** — prevent user confusion
4. **Extract shared utilities** (`_daily_cap_tokens`, `_token_totals`) into a common module
5. **Remove or use `final_stream_usage()`** — dead code cleanup
6. **Add a `schema_version` table** for migration tracking

---

## 7. File Map (for navigation)

```
src/agile_ai_htb/
  __init__.py          — version only
  __main__.py          — entry point
  app.py               — FastAPI factory, lifespan, provider key bridging
  cli.py               — htb operator CLI (serve, seed-demo)
  settings.py          — env-var-based settings
  db.py                — SQLite schema, CRUD, migrations, spend categorization
  auth.py              — portal cookie/bearer auth
  llm.py               — LiteLLM wrapper, usage extraction, cost calculation
  guardrails.py        — YAML config loader, zone math
  governance.py        — 3-layer zone enforcement (prompt, tokens, tools)
  alarms.py            — 7 alarm types, detection logic
  checkpoints.py       — 4 stateless checkpoint evaluators
  estimation.py        — task estimation via control-plane LLM
  execution_backend.py — Local Runner (project connection, profile detection)
  task_launch.py       — task → session orchestration, write-capable launch
  launch_guardrails.py — pre-launch adapter validation
  worker_adapters.py   — adapter builders, verification, model discovery
  demo_seed.py         — synthetic demo data seeder
  demo_worker.py       — lightweight proxy caller for demos
  routes/
    __init__.py        — empty
    alarms.py          — alarm listing, resolution
    portal.py          — HTML portal (dashboard, board, worker settings, project)
    proxy.py           — /v1/chat/completions harness proxy
    sessions.py        — session create, report, artifact, checkpoints
    tasks.py           — task CRUD, estimation, launch, refresh
  templates/
    base.html          — shared layout
    login.html         — portal login
    dashboard.html     — KPI dashboard
    board.html         — kanban task board
    sessions.html      — session list
    session_report.html— session detail report
    alarms.html        — alarm list (open + resolved)
    alarm_card.html    — reusable alarm component
    workers.html       — worker adapter management
    control_plane.html — control-plane model settings
    project.html       — project connection + proof launch

guardrails.yaml        — guardrail configuration

tests/
  test_*.py            — 15+ unit + integration test files
  test_eval_*.py       — 4 behavioral eval files (31 tests)
```

---

*Review conducted by reading all 25 source files, all templates, guardrails.yaml, Dockerfile, and README.md. Tests executed and passing.*
