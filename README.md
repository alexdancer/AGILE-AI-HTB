# AGILE-AI-HTB

A portal-first token-budget governance harness for AI coding agents. AGILE-AI-HTB has two model layers: a control-plane model used by the portal for estimates/planning/reports, and Worker Harness models used by local coding CLIs such as OpenCode, Claude Code, or Codex. It tracks spend by category, enforces Worker execution budgets, and escalates to a human — never the agent — when things go wrong.

Agent-agnostic. Proxy-governed mode works with OpenAI-compatible agents through the Harness Proxy and direct upstream provider clients. Native Worker mode uses the installed Worker CLI's own config/auth and imports trustworthy usage evidence when available.

Current public path: install the `htb` operator CLI, run the local Control Plane/Portal, configure the control-plane model in the Portal, connect a local repo, verify one Worker Adapter, then launch a tiny governed task. Contributor `uv run ...` commands are for repo development, not normal operator setup.

## Four pillars

| Pillar | What it does |
|---|---|
| **Guardrails** | 6 declared constraints enforced at launch, transport, or review depending on tracking mode: daily cap, session cap, budget zones (green/yellow/red), loop detection, session timeout, tool-category limits. Proxy-governed runs can apply transport controls; native-usage runs reconcile after the CLI reports usage. |
| **Checkpoints** | 4 pass/fail evaluations at session boundaries: budget health, stuck-loop score, tool diversity, timeout respect. Stateless — replayable from any session artifact. |
| **Material Handling** | Clean interfaces: AGILE board (Estimated → Running → Review → Done → Blocked), dashboard, session reports, REST API. Launch creates an auditable asynchronous Worker Run; retryable runtime failures return to Estimated with inline evidence. No unestimated Backlog — task intake estimates and budgets before launch. |
| **Alarms** | 7 named alarm types with severity and recommended actions: BUDGET_YELLOW, BUDGET_RED, DAILY_CAP_EXCEEDED, SESSION_CAP_EXCEEDED, LOOP_DETECTED, SESSION_TIMEOUT, TOOL_CATEGORY_BIAS, CHECKPOINT_FAIL. |

**Human-in-the-loop**: the harness constrains the agent, not the human. Every escalation presents a decision — continue, abort, raise budget, adjust guardrail.

## Quick start: first 10 minutes

```bash
# 1. Install the operator CLI.
# Current source install, before PyPI release:
pipx install "git+https://github.com/alexdancer/AI-Harness-Token-Tracker.git"

# After PyPI release this becomes:
# pipx install agile-ai-htb

# One-line bootstrap alternative:
# curl -fsSL https://raw.githubusercontent.com/alexdancer/AI-Harness-Token-Tracker/main/install.sh | sh

# 2. Create local operator config, local secrets, and default guardrails.
htb init

# 3. Start the Portal.
htb serve
```

Then open `http://localhost:8000/login`, use the portal token from `.htb/secrets.env`, and finish setup in the Portal:

1. Open `/settings/control-plane`.
2. Pick the control-plane provider/model, paste the provider API key, save, then click **Test control-plane connection**.
3. Connect a local project from `/projects`.
4. Open `/settings/workers`, choose a Worker Adapter, discover/allow Worker models, then verify token tracking.
5. Launch a tiny task from the project board and review the session report/token evidence.

In another terminal, `htb check` prints redacted `PASS`/`WARN`/`FAIL` setup lines you can paste into support issues.

The control-plane API key powers AGILE-AI-HTB estimation, planning, recommendations, and reports. Native Worker CLIs such as OpenCode, Claude Code, Codex, and Hermes keep their own CLI auth/config; pasting a control-plane key does not configure those tools.

`htb init` creates local-only files under `.htb/`: non-secret `.htb/config.toml`, ignored `.htb/secrets.env`, ignored `.htb/guardrails.yaml`, and a default SQLite path of `.htb/harness.db`. The database file is created when the app initializes. The Portal can save a submitted control-plane API key into `.htb/secrets.env`; it never writes raw key values to `.htb/config.toml` or displays them again.

## What AGILE-AI-HTB governs

AGILE-AI-HTB governs work launched through its AGILE Board and a verified Worker Adapter:

- `proxy_governed`: Worker model traffic flows through the Harness Proxy, so request-time guardrails and token accounting are active during the run.
- `native_usage`: the Worker CLI uses its own auth/config and AGILE-AI-HTB imports trustworthy run-bound usage after the run; accounting is authoritative, but there is no mid-run request throttling.
- `observed_only`: diagnostics only; not normal board-launchable.

It does not govern arbitrary external-agent spend unless traffic goes through the Harness Proxy or the native CLI emits trustworthy usage evidence bound to the launched Worker Run.

## Docker: no-secret Control Plane trial

```bash
# Local Control Plane/Portal. Override this in your shell; do not commit secrets.
export TOKEN_TRACKER_PORTAL_TOKEN="replace-with-local-token"
export AGILE_AI_HTB_CONTROL_PROVIDER="openai"
export AGILE_AI_HTB_CONTROL_MODEL="gpt-5.4-mini"
# Optional later for model-powered estimates/reports:
# export AGILE_AI_HTB_CONTROL_API_KEY="replace-with-provider-key"

docker-compose up -d --build
curl http://localhost:8000/health
# {"status":"ok"}

# Inspect setup from inside the container; exits nonzero until required secrets are set.
docker-compose exec agile-ai-htb htb check || true

# Full local Docker smoke: build/start, /health, /login,
# container recreation DB persistence, cleanup.
# Stops and recreates this repo's Compose service; named volumes are kept.
scripts/docker-smoke.sh
```

Docker runs the containerized Control Plane/Portal with SQLite at `/data/harness.db`. The no-secret path proves image build/start, `/health`, `/login`, and database persistence. Model-powered estimates, provider connection tests, and real Worker verification require later credential setup.

Docker does not automatically get host-installed OpenCode, Claude Code, Codex, Hermes, local repo paths, or host credentials; Worker launch readiness still depends on Worker Adapter setup and tracking-mode checks. Docker control-plane env vars configure AGILE-AI-HTB estimation/planning/reporting only, not native Worker CLI auth.

More setup details:

- [Install options](docs/INSTALL.md)
- [Getting started](docs/GETTING_STARTED.md)
- [Worker Adapter setup matrix](docs/WORKER_ADAPTER_SETUP.md)
- [Setup support checklist](docs/SETUP_SUPPORT_CHECKLIST.md)

## The demo loop

1. **Type a task** — "Add a save command to the CLI" in the board intake form
2. **Estimate** — Control-plane LLM (real direct-provider call) returns token budget, complexity, model recommendation, confidence. Tracked as `usage_kind=estimation`.
3. **Launch** — Verified Worker adapter passes launch guardrails. Native mode launches the selected discovered Worker model; proxy-governed mode routes through the Harness Proxy. The portal returns immediately with the task in `Running`.
4. **Worker runs async** — Each launch creates a persisted Worker Run with command plan metadata, stdout/stderr evidence, timeout/error details, and token/usage evidence. Successful runs move to `Review`; retryable launch/runtime failures return to `Estimated`; hard safety failures move to `Blocked`.
5. **Report** — Session artifact shows token totals, tool breakdown, zone snapshots, alarms, checkpoint results, and Worker Run evidence.

Use `.htb/config.toml` for the control-plane provider/model. Keep `AGILE_AI_HTB_CONTROL_API_KEY` in ignored `.htb/secrets.env`, an environment variable, or paste it through `/settings/control-plane`; the portal writes key values only to ignored local secret storage. `PROVIDER_API_KEY` remains a compatibility alias for older setups only; native OpenCode mode uses the installed `opencode` CLI's own config/auth.

### Local OpenCode read-only proof

Initialize the operator config, start the portal, provide the control-plane API key through `.htb/secrets.env` or `/settings/control-plane`, then run the script:

```bash
htb init
htb serve

# second terminal
htb check
PROJECT_ROOT=$PWD scripts/local-opencode-readonly-demo.sh
```

Flow: tests control-plane connection → discovers OpenCode Worker models from the installed CLI → verifies `native_usage` tracking → connects local project → launches read-only proof. No OpenAI-style Worker credential is required for native OpenCode; configure OpenCode itself first. If OpenCode cannot emit trustworthy run-bound native usage evidence, the adapter remains diagnostic/`observed_only` and is not launchable from the AGILE Board.

### Long OpenCode comparison baseline

For the long comparison demo, run the same synthetic task directly through OpenCode and then through AGILE-AI-HTB:

- Task: [`demo_tasks/DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md`](demo_tasks/DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md)
- Runbook: [`docs/DEMO_2099_OPENCODE_COMPARISON_RUNBOOK.md`](docs/DEMO_2099_OPENCODE_COMPARISON_RUNBOOK.md)
- Direct baseline evidence: `.demo/opencode-comparison/evidence/direct-opencode-raw-events.jsonl`

Direct OpenCode baseline already recorded from `openai/gpt-5.5` with `--variant high`:

| Metric | Result |
|---|---:|
| Raw JSONL events | 134 |
| Evidence size | 330,303 bytes |
| Session | `ses_113fd6d71ffeE3YVEEQk7PvcDA` |
| Usage records | 36 |
| Cumulative token units | 1,601,736 |
| Input tokens | 63,303 |
| Output tokens | 22,078 |
| Reasoning tokens | 5,955 |
| Generated target tests | 16 passed |

AGILE-AI-HTB portal run recorded in `.demo/opencode-comparison/harness.db`:

| Metric | Result |
|---|---:|
| Task breakdown reviews accepted | 1 |
| Board tasks created | 7 |
| Completed Worker runs | 6 |
| Final board state | 6 Review, 1 Blocked |
| Worker budget configured | 2,500,000 daily / 400,000 session |
| Control-plane/task-breakdown tokens | 15,776 |
| Worker execution tokens | 76,740 |
| Total ledger tokens | 92,516 |
| Alarms generated | 0 |
| Harness target tests | 5 passed |

Competency comparison is measured by an external smoke check, not by either project's self-written tests:

```bash
python3 scripts/compare-opencode-demo-projects.py
```

| Criterion | Direct OpenCode | AGILE-AI-HTB OpenCode |
|---|---:|---:|
| External acceptance checks | 15/15 passed | 15/15 passed |
| Project self-tests | 16 passed | 5 passed |
| Python files | 14 | 6 |
| Test files | 7 | 1 |
| Recorded token usage | 1,601,736 cumulative OpenCode units | 92,516 ledger tokens |

Result: both projects satisfy the external smoke acceptance path, but deeper review found Direct OpenCode materially stronger on implementation quality. Direct produced the broader, more spec-complete project and test suite; AGILE-AI-HTB produced a smaller happy-path implementation while adding estimate, budget, launch, ledger, and review evidence around the run.

Review caveat: the external smoke check is intentionally broad. It does not catch every contract detail; the harness-launched project missed stricter report/schema details such as the expected JSON report keys, `DEMO-DUPE-2099-*` duplicate IDs, richer Markdown report sections, and severity/date list ordering. The fair demo claim is governance and auditability around Worker execution, not that the harness made the Worker produce better code in this run.

The cumulative token total is OpenCode event-stream accounting from `step_finish -> part.tokens`, including cache-read usage. The comparison claim is governance, not magic compression: direct OpenCode shows uncontrolled baseline usage; AGILE-AI-HTB adds estimate, budget gate, launch evidence, token ledger, alarms, and review workflow around the same Worker task.

## Configuration

For normal local runs, use `/settings/control-plane` to change the control-plane provider, model, base URL, API key env name, or API key value live. The portal saves non-secrets to `.htb/config.toml`, writes submitted key values only to ignored local secret storage, and marks the connection as `needs test` until you rerun the control-plane test.

Use environment variables mainly for Docker, CI, or headless operation:

| Setting | Purpose |
|---|---|
| `TOKEN_TRACKER_PORTAL_TOKEN` | Portal login token |
| `AGILE_AI_HTB_CONTROL_PROVIDER` | Control-plane provider: `openai`, `anthropic`, or `openai-compatible` |
| `AGILE_AI_HTB_CONTROL_MODEL` | Control-plane model for estimates, breakdowns, recommendations, and reports |
| `AGILE_AI_HTB_CONTROL_BASE_URL` | Required for OpenAI-compatible endpoints; optional otherwise |
| `AGILE_AI_HTB_CONTROL_API_KEY` | Control-plane provider API key |

Native Worker CLIs keep their own auth/config. See [Getting started](docs/GETTING_STARTED.md) and [Worker Adapter setup](docs/WORKER_ADAPTER_SETUP.md) for setup details.

## Tests

```bash
# Full suite
uv run pytest -q

# Contributor CLI smoke from a checkout
uv run htb --help

# Focused suites
uv run pytest tests/portal tests/api tests/workers -q
uv run pytest tests/evals -v
uv run pytest tests/smoke -q
```

All tests use fake LLM clients. Zero provider calls. Zero cost.

## Project structure

```
src/agile_ai_htb/
  app.py              FastAPI app factory + /health
  cli.py              htb operator CLI (init, serve, check, seed-demo)
  db.py               SQLite persistence, schema, migrations
  auth.py             Portal cookie auth
  settings.py         Env-var settings
  guardrails.py       Guardrail config loader + zone math
  operator_config.py  .htb config/secrets helpers
  governance.py       Three-layer enforcement engine
  alarms.py           7 alarm types + detection logic
  checkpoints.py      4 stateless checkpoint evaluators
  estimation.py       Estimator LLM with structured output
  task_launch.py      Task → session orchestration
  launch_guardrails.py Pre-launch validation
  worker_adapters.py  Adapter presets + subprocess runner
  routes/             FastAPI route modules
  templates/          Jinja2 HTML templates
  defaults/           Default guardrail YAML bundled in package
tests/
  api/                REST/API behavior tests
  portal/             Server-rendered Portal tests
  workers/            Worker adapter and launch tests
  budgeting/          Budget, guardrail, alarm, checkpoint tests
  evals/              Behavioral evals
  demo/               Synthetic demo invariant tests
  smoke/              End-to-end smoke tests
CONTEXT.md            Domain glossary
docs/
  GETTING_STARTED.md  First-run operator guide
  INSTALL.md          pipx, curl installer, and Homebrew status
  WORKER_ADAPTER_SETUP.md
  SETUP_SUPPORT_CHECKLIST.md
  TODO.md             Human-readable next work
  MCP_AGENT_HARNESS_TODO.md
  HARNESS.md          Architecture reference
  DEMO_2099_OPENCODE_COMPARISON_RUNBOOK.md
install.sh            uv-tool/pipx bootstrap installer
packaging/homebrew/   Future Homebrew formula scaffold
```
