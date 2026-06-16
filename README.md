# AGILE-AI-HTB

A portal-first token-budget governance harness for AI coding agents. AGILE-AI-HTB has two model layers: a control-plane model used by the portal for estimates/planning/reports, and Worker Harness models used by local coding CLIs such as OpenCode, Claude Code, or Codex. It tracks spend by category, enforces Worker execution budgets, and escalates to a human — never the agent — when things go wrong.

Agent-agnostic. Proxy-governed mode works with OpenAI-compatible agents through LiteLLM. Native Worker mode uses the installed harness's own CLI/config/auth and imports trustworthy usage evidence when available.

## Four pillars

| Pillar | What it does |
|---|---|
| **Guardrails** | 6 declared constraints enforced at the transport level: daily cap, session cap, budget zones (green/yellow/red), loop detection, session timeout, tool-category limits. Three-layer graduated enforcement per zone — system prompt rewrite, max_tokens clamping, tool restrictions. |
| **Checkpoints** | 4 pass/fail evaluations at session boundaries: budget health, stuck-loop score, tool diversity, timeout respect. Stateless — replayable from any session artifact. |
| **Material Handling** | Clean interfaces: AGILE board (Estimated → Ready → Running → Review → Done → Blocked), dashboard, session reports, REST API. No unestimated Backlog — task intake estimates and budgets before launch. |
| **Alarms** | 7 named alarm types with severity and recommended actions: BUDGET_YELLOW, BUDGET_RED, DAILY_CAP_EXCEEDED, SESSION_CAP_EXCEEDED, LOOP_DETECTED, SESSION_TIMEOUT, TOOL_CATEGORY_BIAS, CHECKPOINT_FAIL. |

**Human-in-the-loop**: the harness constrains the agent, not the human. Every escalation presents a decision — continue, abort, raise budget, adjust guardrail.

## Quick start

```bash
# Clone and enter
git clone https://github.com/alexdancer/AI-Harness-Token-Tracker.git
cd AI-Harness-Token-Tracker

# Create venv and install
python3 -m venv .venv
.venv/bin/pip install -e ".[test]"

# Run tests (zero provider calls — all fakes)
.venv/bin/python -m pytest -q

# Start the portal
export TOKEN_TRACKER_PORTAL_TOKEN=demo-token
.venv/bin/htb serve --host 127.0.0.1 --port 8000

# In another terminal, seed demo tasks
.venv/bin/htb seed-demo

# Open http://localhost:8000/login — log in with "demo-token"
```

## Docker

```bash
docker compose up -d
curl http://localhost:8000/health
# {"status":"ok"}

# Seed demo data (includes verified worker adapter)
docker compose exec agile-ai-htb htb seed-demo
```

## The demo loop

1. **Type a task** — "Add a save command to the CLI" in the board intake form
2. **Estimate** — Estimator LLM (real LiteLLM call) returns token budget, complexity, model recommendation, confidence. Tracked as `usage_kind=estimation`.
3. **Launch** — Verified Worker adapter passes launch guardrails. Native mode launches the selected discovered Worker model; proxy-governed mode routes through the Harness Proxy.
4. **Worker runs** — Worker execution tokens are recorded as Worker spend. Control-plane estimation/reporting spend stays separate.
5. **Report** — Session artifact shows token totals, tool breakdown, zone snapshots, alarms, checkpoint results.

Set `AGILE_AI_HTB_CONTROL_API_KEY` for real control-plane LLM calls. `PROVIDER_API_KEY` remains a compatibility alias for older deployments and proxy-governed Worker mode, but native OpenCode mode uses the installed `opencode` CLI's own config/auth.

### Local OpenCode read-only proof

Start portal with Local Runner enabled, then run script:

```bash
export TOKEN_TRACKER_PORTAL_TOKEN=demo-token
export AGILE_AI_HTB_CONTROL_API_KEY=your-control-plane-key
uv run htb serve --local-runner --host 127.0.0.1 --port 8000

# second terminal
export TOKEN_TRACKER_PORTAL_TOKEN=demo-token
PROJECT_ROOT=$PWD scripts/local-opencode-readonly-demo.sh
```

Flow: tests control-plane connection → discovers OpenCode Worker models → verifies native usage tracking → connects local project → launches read-only proof. No OpenAI-style Worker credential is required for native OpenCode; configure OpenCode itself first.

## Deploy to Render

One-click Blueprint deploy via `render.yaml` at the repo root.

1. Push to GitHub
2. Render dashboard → New → Blueprint → connect repo
3. Create 1GB disk named `harness-data` (mount: `/data`)
4. Set secrets in dashboard: `TOKEN_TRACKER_PORTAL_TOKEN`, `PROVIDER_API_KEY`
5. Deploy → `https://agile-ai-htb.onrender.com/login`

Full runbook: [`docs/DEPLOY.md`](docs/DEPLOY.md)

## Env vars

| Variable | Default | Purpose |
|---|---|---|
| `TOKEN_TRACKER_DATABASE_PATH` | `harness.db` | SQLite path (`/data/harness.db` in Docker) |
| `TOKEN_TRACKER_GUARDRAILS_PATH` | `guardrails.yaml` | Guardrail config |
| `TOKEN_TRACKER_PORTAL_TOKEN` | — | Portal login/bearer token (required) |
| `TOKEN_TRACKER_PORTAL_COOKIE_SECURE` | `false` | Set `true` for HTTPS |
| `TOKEN_TRACKER_CONTROL_PLANE_MODEL` / `AGILE_AI_HTB_CONTROL_MODEL` | `gpt-4o-mini` | Control-plane model for estimates, summaries, and reports |
| `AGILE_AI_HTB_CONTROL_API_KEY_ENV` | `AGILE_AI_HTB_CONTROL_API_KEY` | Env var name holding control-plane API key |
| `AGILE_AI_HTB_CONTROL_API_KEY` | — | Control-plane model API key |
| `TOKEN_TRACKER_PROVIDER_API_KEY_ENV` | `PROVIDER_API_KEY` | Legacy/proxy-governed Worker provider-key env var name |
| `PROVIDER_API_KEY` | — | Compatibility alias; not required for native OpenCode Worker mode |

## Tests

```bash
# Full suite (197 tests, 0 failures)
.venv/bin/python -m pytest -q

# Behavioral evals only (31 tests)
.venv/bin/python -m pytest tests/test_eval_*.py -v

# Proxy token tracking evals
.venv/bin/python -m pytest tests/test_eval_proxy_token_tracking.py -v

# Zone transition evals
.venv/bin/python -m pytest tests/test_eval_zone_transitions.py -v

# Alarm firing evals
.venv/bin/python -m pytest tests/test_eval_alarm_firing.py -v

# Estimator evals
.venv/bin/python -m pytest tests/test_eval_estimator.py -v
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
docs/
  CONTEXT.md          Domain glossary
  PRD.md              Product requirements
  IMPLEMENTATION-PLAN.md  Implementation plan + status
  HARNESS.md          Architecture reference
  DEMO.md             Demo scenario
  DEMO_VIDEO_SCRIPT.md 6-minute video script
  DEPLOY.md           Render deployment runbook
```
