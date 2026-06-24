# AGILE-AI-HTB

A portal-first token-budget governance harness for AI coding agents. AGILE-AI-HTB has two model layers: a control-plane model used by the portal for estimates/planning/reports, and Worker Harness models used by local coding CLIs such as OpenCode, Claude Code, or Codex. It tracks spend by category, enforces Worker execution budgets, and escalates to a human — never the agent — when things go wrong.

Agent-agnostic. Proxy-governed mode works with OpenAI-compatible agents through the Harness Proxy and direct upstream provider clients. Native Worker mode uses the installed harness's own CLI/config/auth and imports trustworthy usage evidence when available.

## Four pillars

| Pillar | What it does |
|---|---|
| **Guardrails** | 6 declared constraints enforced at the transport level: daily cap, session cap, budget zones (green/yellow/red), loop detection, session timeout, tool-category limits. Three-layer graduated enforcement per zone — system prompt rewrite, max_tokens clamping, tool restrictions. |
| **Checkpoints** | 4 pass/fail evaluations at session boundaries: budget health, stuck-loop score, tool diversity, timeout respect. Stateless — replayable from any session artifact. |
| **Material Handling** | Clean interfaces: AGILE board (Estimated → Running → Review → Done → Blocked), dashboard, session reports, REST API. Launch creates an auditable asynchronous Worker Run; retryable runtime failures return to Estimated with inline evidence. No unestimated Backlog — task intake estimates and budgets before launch. |
| **Alarms** | 7 named alarm types with severity and recommended actions: BUDGET_YELLOW, BUDGET_RED, DAILY_CAP_EXCEEDED, SESSION_CAP_EXCEEDED, LOOP_DETECTED, SESSION_TIMEOUT, TOOL_CATEGORY_BIAS, CHECKPOINT_FAIL. |

**Human-in-the-loop**: the harness constrains the agent, not the human. Every escalation presents a decision — continue, abort, raise budget, adjust guardrail.

## Quick start

```bash
# Clone and enter
git clone https://github.com/alexdancer/AI-Harness-Token-Tracker.git
cd AI-Harness-Token-Tracker

# Install with uv (preferred) or pip
uv pip install -e ".[test]"
# or: python3 -m venv .venv && .venv/bin/pip install -e ".[test]"

# Run tests (zero provider calls — all fakes)
uv run python -m pytest -q

# Configure local operator defaults (non-secrets only)
uv run htb init
# Edit .htb/secrets.env once, then start the portal
uv run htb serve

# In another terminal, verify setup; optionally seed demo tasks
uv run htb check
uv run htb seed-demo

# Open http://localhost:8000/login — log in with your portal token
```

## Docker

```bash
docker-compose up -d
curl http://localhost:8000/health
# {"status":"ok"}

# Seed demo data (includes verified worker adapter)
docker-compose exec agile-ai-htb htb seed-demo
```

## The demo loop

1. **Type a task** — "Add a save command to the CLI" in the board intake form
2. **Estimate** — Control-plane LLM (real direct-provider call) returns token budget, complexity, model recommendation, confidence. Tracked as `usage_kind=estimation`.
3. **Launch** — Verified Worker adapter passes launch guardrails. Native mode launches the selected discovered Worker model; proxy-governed mode routes through the Harness Proxy. The portal returns immediately with the task in `Running`.
4. **Worker runs async** — Each launch creates a persisted Worker Run with command plan metadata, stdout/stderr evidence, timeout/error details, and token/usage evidence. Successful runs move to `Review`; retryable launch/runtime failures return to `Estimated`; hard safety failures move to `Blocked`.
5. **Report** — Session artifact shows token totals, tool breakdown, zone snapshots, alarms, checkpoint results, and Worker Run evidence.

Use `.htb/config.toml` for the control-plane provider/model and `.htb/secrets.env` for `AGILE_AI_HTB_CONTROL_API_KEY` in the local operator flow. `PROVIDER_API_KEY` remains a compatibility alias for older deployments only; native OpenCode mode uses the installed `opencode` CLI's own config/auth.

### Local OpenCode read-only proof

Initialize the operator config, edit `.htb/secrets.env`, start the portal, then run the script:

```bash
uv run htb init
# Edit .htb/secrets.env and replace AGILE_AI_HTB_CONTROL_API_KEY=<your-control-plane-api-key>
uv run htb serve

# second terminal
uv run htb check
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

## Deploy to Render

One-click Blueprint deploy via `render.yaml` at the repo root.

1. Push to GitHub
2. Render dashboard → New → Blueprint → connect repo
3. Create 1GB disk named `harness-data` (mount: `/data`)
4. Set secrets in dashboard: `TOKEN_TRACKER_PORTAL_TOKEN`, `AGILE_AI_HTB_CONTROL_API_KEY`
5. Deploy → `https://agile-ai-htb.onrender.com/login`

Full runbook: [`docs/DEPLOY.md`](docs/DEPLOY.md)

## Env vars

| Variable | Default | Purpose |
|---|---|---|
| `TOKEN_TRACKER_DATABASE_PATH` | `harness.db` | SQLite path (`/data/harness.db` in Docker) |
| `TOKEN_TRACKER_GUARDRAILS_PATH` | `guardrails.yaml` | Guardrail config |
| `TOKEN_TRACKER_PORTAL_TOKEN` | — | Portal login/bearer token (required) |
| `TOKEN_TRACKER_PORTAL_COOKIE_SECURE` | `false` | Set `true` for HTTPS |
| `TOKEN_TRACKER_CONTROL_PLANE_MODEL` / `AGILE_AI_HTB_CONTROL_MODEL` | `gpt-4o-mini` | Control-plane model for estimates, summaries, and reports. Local/demo runs should set `gpt-5.4-mini`. |
| `TOKEN_TRACKER_TASK_BREAKDOWN_MODEL` / `AGILE_AI_HTB_TASK_BREAKDOWN_MODEL` | control-plane model | Optional Task Breakdown Agent model. Falls back to the control-plane model and records spend as control-plane orchestration tokens labeled `task_breakdown`, not Worker Adapter spend. |
| `TOKEN_TRACKER_CONTROL_PLANE_PROVIDER` / `AGILE_AI_HTB_CONTROL_PROVIDER` | `openai` | Direct upstream provider (`openai`, `openai-compatible`, or `anthropic`) |
| `AGILE_AI_HTB_CONTROL_BASE_URL` | — | Optional base URL for OpenAI-compatible upstreams |
| `AGILE_AI_HTB_CONTROL_API_KEY_ENV` | `AGILE_AI_HTB_CONTROL_API_KEY` | Env var name holding control-plane API key |
| `AGILE_AI_HTB_CONTROL_API_KEY` | — | Control-plane model API key |
| `TOKEN_TRACKER_PROVIDER_API_KEY_ENV` | `PROVIDER_API_KEY` | Legacy control-plane provider-key env var name |
| `PROVIDER_API_KEY` | — | Compatibility alias; not required for native OpenCode Worker mode |

## Tests

```bash
# Full suite
uv run python -m pytest -q

# Behavioral evals only (31 tests)
uv run python -m pytest tests/test_eval_*.py -v

# Proxy token tracking evals
uv run python -m pytest tests/test_eval_proxy_token_tracking.py -v

# Zone transition evals
uv run python -m pytest tests/test_eval_zone_transitions.py -v

# Alarm firing evals
uv run python -m pytest tests/test_eval_alarm_firing.py -v

# Estimator evals
uv run python -m pytest tests/test_eval_estimator.py -v
```

All tests use fake LLM clients. Zero provider calls. Zero cost.

## Project structure

```
src/agile_ai_htb/
  app.py              FastAPI app factory + /health
  cli.py              htb operator CLI (serve, seed-demo)
  db.py               SQLite persistence, schema, migrations
  auth.py             Portal cookie auth
  settings.py         Env-var settings
  guardrails.py       Guardrail config loader + zone math
  governance.py       Three-layer enforcement engine
  alarms.py           7 alarm types + detection logic
  checkpoints.py      4 stateless checkpoint evaluators
  estimation.py       Estimator LLM with structured output
  task_launch.py      Task → session orchestration
  launch_guardrails.py Pre-launch validation
  worker_adapters.py  Adapter presets + subprocess runner
  demo_worker.py      Lightweight proxy caller for demos
  demo_seed.py        Synthetic DEMO task + adapter seeding
  routes/             FastAPI route modules
  templates/          Jinja2 HTML templates
tests/
  test_eval_*.py      31 behavioral evals
  test_*.py           Unit + integration tests
CONTEXT.md            Domain glossary
docs/
  PRD.md              Product requirements
  IMPLEMENTATION-PLAN.md  Implementation plan + status
  HARNESS.md          Architecture reference
  DEMO.md             Demo scenario
  DEMO_VIDEO_SCRIPT.md 6-minute video script
  DEPLOY.md           Render deployment runbook
```
