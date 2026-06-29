# AGILE-AI-HTB

AGILE-AI-HTB is a local, portal-first governance harness for AI coding agents.

It does **not** replace OpenCode, Claude Code, Codex, Hermes, or another coding CLI. It wraps those tools with a board, budgets, launch checks, token evidence, session reports, and human review.

Use it when you want a coding agent workflow that is easier to inspect:

- estimate work before launch
- break larger plans into smaller governed slices
- run coding agents from a project board
- record Worker Run evidence, stdout/stderr, token usage, and review state
- keep budget overrides and final acceptance in human hands

## Current supported path

Today the supported operator path is local all-in-one mode:

```text
installed htb CLI
  -> local Portal / Control Plane
  -> local repo connection
  -> verified local Worker CLI, such as OpenCode
  -> session report and token evidence
```

The Worker CLI keeps its own auth/config. AGILE-AI-HTB configures the control-plane model separately for estimates, planning, recommendations, summaries, and reports.

AGILE-AI-HTB only governs work launched through its own board and a verified Worker Adapter. It does not govern arbitrary external agent spend.

## Install

Recommended source install before PyPI release:

```bash
pipx install "git+https://github.com/alexdancer/AI-Harness-Token-Tracker.git"
htb init
htb serve
```

One-line bootstrap alternative:

```bash
curl -fsSL https://raw.githubusercontent.com/alexdancer/AI-Harness-Token-Tracker/main/install.sh | sh
htb init
htb serve
```

After the package is published to PyPI, the intended command is:

```bash
pipx install agile-ai-htb
htb init
htb serve
```

For contributors working from a checkout:

```bash
uv run htb init
uv run htb serve
```

More install detail: [docs/INSTALL.md](docs/INSTALL.md).

## First run

1. Start the Portal:
   ```bash
   htb serve
   ```
2. Open `http://localhost:8000/login`.
3. Use the portal token from ignored `.htb/secrets.env`.
4. Open `/settings/control-plane`.
5. Pick a control-plane provider/model, paste the provider API key, save, then test the connection.
6. Connect a local repository from `/projects`.
7. Open `/settings/workers`, choose a Worker Adapter, discover/allow Worker models, then verify token tracking.
8. Launch a tiny task from the project board.
9. Review the session report and token evidence before marking the task done.

For redacted support status:

```bash
htb check
```

## How the workflow works

1. **Create a task** on the project board.
2. **Estimate** with the control-plane model.
3. **Launch** through a verified Worker Adapter.
4. **Run async** while the Portal stays responsive.
5. **Review evidence**: command plan, stdout/stderr, token usage, alarms, and session report.
6. **Accept or block** as the human operator.

Board states are:

```text
Estimated -> Running -> Review -> Done
                         -> Blocked
```

## Basic architecture

AGILE-AI-HTB has four main pieces:

| Piece | Role |
|---|---|
| **Portal / Control Plane** | Browser UI and API for setup, estimates, project boards, launch, reports, budgets, and review. |
| **Local Runner** | Runs near your local repository so Worker CLIs can see local files, git state, and their own credentials. In local mode it runs inside the same app process. |
| **Worker Adapter** | Integration for a coding CLI such as OpenCode, Claude Code, Codex, or Hermes. Adapter verification proves the CLI can run and produce trustworthy usage evidence for the selected model. |
| **Token ledger and reports** | SQLite-backed records for estimates, Worker Runs, token evidence, alarms, checkpoints, and session artifacts. |

There are two model layers:

| Layer | Used for | Auth/config |
|---|---|---|
| **Control Plane model** | estimates, planning, task breakdown, recommendations, reports | configured in `/settings/control-plane` or local config/secrets |
| **Worker model** | the actual coding task | configured by the native Worker CLI |

Pasting a control-plane API key does not configure OpenCode, Claude Code, Codex, Hermes, or another Worker CLI.

## Local files and configuration

`htb init` creates local-only state under `.htb/`:

| File | Purpose |
|---|---|
| `.htb/config.toml` | non-secret local config |
| `.htb/secrets.env` | ignored portal token and control-plane API key storage |
| `.htb/guardrails.yaml` | ignored default guardrail config |
| `.htb/harness.db` | default SQLite database path, created when the app initializes |

For normal local use, prefer the Portal settings screens. Environment variables are mainly for CI, headless runs, or compatibility.

Common environment variables:

| Variable | Purpose |
|---|---|
| `TOKEN_TRACKER_PORTAL_TOKEN` | Portal login token |
| `AGILE_AI_HTB_CONTROL_PROVIDER` | Control-plane provider, such as `openai`, `anthropic`, or `openai-compatible` |
| `AGILE_AI_HTB_CONTROL_MODEL` | Control-plane model |
| `AGILE_AI_HTB_CONTROL_BASE_URL` | Base URL for OpenAI-compatible providers |
| `AGILE_AI_HTB_CONTROL_API_KEY` | Control-plane provider API key |

The Portal writes submitted API keys only to ignored local secret storage and does not display raw key values again.

## Current limits

- The main supported path is local all-in-one mode.
- Worker launch readiness depends on local repo access, git state, installed Worker CLIs, and native CLI auth/config.
- Hosted workspaces, a fuller CLI, MCP access, PyPI release, and Homebrew install are future work.

## More docs

- [Getting started](docs/GETTING_STARTED.md)
- [Install options](docs/INSTALL.md)
- [Worker Adapter setup](docs/WORKER_ADAPTER_SETUP.md)
- [Setup support checklist](docs/SETUP_SUPPORT_CHECKLIST.md)
- [Project TODO](docs/TODO.md)

## Tests

```bash
uv run pytest -q
```

Focused contributor checks:

```bash
uv run htb --help
uv run pytest tests/portal tests/api tests/workers -q
uv run pytest tests/evals -v
uv run pytest tests/smoke -q
```

Tests use fake LLM clients. They do not make provider calls.
