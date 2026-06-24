# Demo Scenario: CLI Snippet Manager

A synthetic project that a coding agent builds live under harness governance. The project is a Python CLI tool (`snip`) for managing code snippets — small enough to complete in a demo but with enough surface area for tasks of varying complexity.

For a longer token-usage comparison between direct OpenCode and AGILE-AI-HTB-launched OpenCode, use `demo_tasks/DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md` with the runbook at `docs/DEMO_2099_OPENCODE_COMPARISON_RUNBOOK.md`. That comparison keeps the control-plane/orchestrator model separate from the OpenCode Worker model and demonstrates budget governance, usage authority, launch/review lifecycle, and measured outcomes under a configured harness Worker budget; it does not claim the same full OpenCode prompt automatically uses fewer Worker tokens through `native_usage`.

## The Project

**`snip`** — a CLI snippet manager. Commands: `snip save`, `snip list`, `snip search`, `snip delete`. Snippets stored as JSON files in `~/.snip/`. Each snippet has a title, language tag, and body.

**Starting state**: A bare scaffold. `cli.py` has argument parsing via argparse but no commands implemented. `store.py` has a `SnippetStore` class with `__init__` but no methods. `pyproject.toml` exists. No tests, no README.

---

## Demo Tasks

The AGILE board is pre-populated with 6 fully synthetic `DEMO_TASK_2099_*` tasks spanning all three complexity tiers. The local demo defaults to the `demo_worker` adapter with `gpt-5.4-mini`; real OpenCode/Codex/Claude Code proof is optional and depends on the user's installed CLI/auth.

### Easy tasks

| # | Task | Est. tokens | Complexity | Recommended model |
|---|---|---|---|---|
| T1 | **Implement `snip save`** — accept title, language, and body via CLI args; write snippet to the store | 8K | Simple | gpt-5.4-mini |
| T2 | **Add a `--color` flag** — support `--color/--no-color` for terminal output; pass through to `rich.print` | 5K | Simple | gpt-5.4-mini |

### Medium tasks

| # | Task | Est. tokens | Complexity | Recommended model |
|---|---|---|---|---|
| T3 | **Implement `snip list` with filters** — list all snippets; support `--language` and `--tag` filters; format as a table with `rich` | 25K | Modest | gpt-5.4-mini |
| T4 | **Add fuzzy search via `snip search`** — accept a query string; use `thefuzz` for fuzzy matching on title and body; rank and display results | 35K | Modest | gpt-5.4-mini |

### Complex tasks

| # | Task | Est. tokens | Complexity | Recommended model |
|---|---|---|---|---|
| T5 | **Add SQLite backend with migration** — replace JSON file store with SQLite via `sqlite3`; write a migration that imports existing JSON snippets; add `--db-path` flag | 90K | Complex | gpt-5.4-mini |
| T6 | **Add `snip share` with gist integration** — accept a snippet ID; push to GitHub Gist via the GitHub API; require a `GITHUB_TOKEN` env var; return the gist URL | 80K | Complex | gpt-5.4-mini |

---

## Demo Flow

The presenter walks through the harness as the agent works through the tasks. Each beat shows a specific harness capability.

### Beat 0: Setup (30 seconds)

- Show the operator setup path: `uv run htb init`, edit `.htb/secrets.env`, `uv run htb serve`, then `uv run htb check`. If using Docker on this Mac, use `docker-compose`, not `docker compose`.
- Portal at `http://localhost:8000` — dashboard empty, 0 sessions
- Show `guardrails.yaml`: daily cap 200K, session cap 50K, zones configured
- AGILE board with all 6 tasks seeded in Estimated column, awaiting Worker Adapter verification

### Beat 1: Estimation & Model Routing (60 seconds)

- Click **Estimate task** for T1 ("Implement `snip save`")
- Portal calls the Estimator LLM via `/estimate` — harness returns structured output: **simple** complexity, **gpt-5.4-mini** recommended, **8K token** estimate, confidence value, and rationale.
- Task moves to **Estimated** column with estimate/model metadata
- Click **Estimate task** for T5 ("SQLite backend") — Estimator LLM classifies it as **complex**, recommends a Worker model from the selected adapter's supported models, and estimates about **90K tokens**.
- **Budget clamp demo**: artificially lower daily budget to 50K, then estimate or launch T5 again. Harness warns that the estimate exceeds remaining budget. For `native_usage`, a budget override also requires explicit acknowledgement that native CLI requests cannot be throttled mid-run.
- Show the budget bar: "0 / 200,000 daily tokens (resets in 7h 15m)"
- Show Orchestration Tokens row: estimator spend tracked as `usage_kind=estimation`, separate from Worker Tokens

### Beat 2: Green Zone — Normal Operation (90 seconds)

- Reset budget to 200K
- Dispatch T1 (save command, Haiku, 8K estimated)
- Session starts. Agent works in **green zone**.
- Live dashboard shows: green bar, token burn counter ticking up, tool calls appearing
- Agent uses all tools freely: `read_file` (reads cli.py), `patch` (adds save logic), `terminal` (runs `snip save "hello" py "print('hi')"`), verifies output
- Session completes: **7.2K actual tokens**, under estimate, green badge
- Card lands in Done column with "7.2K / 8K estimated ✓"

### Beat 3: Yellow Zone — Governance in Action (90 seconds)

- Pre-spend ~80K tokens across a couple more tasks to push the daily budget into yellow zone
- Dispatch T3 (list command, Sonnet, 25K estimated)
- Session starts. Daily budget is now at 45% — still green for the session.
- Agent works. Mid-session, daily budget crosses 60% → **yellow zone**.
- **Layer 1 visible**: Agent's system prompt changes on the next turn — now says "Budget is limited. Prioritize the core task. Be concise."
- **Layer 2 visible**: `max_tokens` drops from 4096 to 2048 — agent's responses visibly shorten
- **Layer 3 visible**: `web_search` and `browser_*` tools removed from the tool list — if the agent tries to search, it can't; the tools don't exist
- **Alarm fires**: `BUDGET_YELLOW` appears in the alarm log with LOW severity
- Agent continues working with constraints and completes the task
- Session report shows the zone transition and tool restrictions

### Beat 4: Red Zone — Critical Governance (60 seconds)

- Dispatch T4 (search command, Sonnet, 35K estimated) — budget is already in yellow
- Agent enters **red zone** during the session (daily budget >85%)
- **Layer 1**: System prompt now: "Budget critical. Output only the final deliverable. If you cannot finish in two turns, deliver what you have."
- **Layer 2**: `max_tokens` dropped to 1024
- **Layer 3**: Only `read_file`, `patch`, `terminal` remain — all exploration tools gone
- Agent forced to work fast and lean; delivers a working but bare `snip search` implementation
- **Alarm fires**: `BUDGET_RED` (MEDIUM) + macOS notification shown
- Session completes. Card lands in Review (checkpoint failed — tool diversity score low because agent was restricted)

### Beat 5: Midnight Reset (45 seconds)

- Simulate midnight by adjusting system clock or manually resetting the daily counter
- Portal shows: "Daily budget reset. 0 / 200,000 tokens (resets in 23h 59m)."
- If a session had been running in red zone at midnight, show it returning to green — agent regains full tools and max_tokens without restart
- Alarm log shows the reset event

### Beat 6: Second-Worker Swap / Bonus (45 seconds)

- Go to the Done column, find T1 (completed with Haiku)
- Click "Re-run with..." → select **GPT-4o-mini**
- Same task, same guardrails, different agent — zero harness changes
- Session runs. Both sessions appear side-by-side in history: "T1 — Haiku — 7.2K tokens" and "T1 — GPT-4o-mini — 6.8K tokens"
- Compare the outputs: both correct, different style — proves portability

### Beat 7: Dashboard Tour (30 seconds)

- Full dashboard: 6+ sessions completed, token burn timeline chart, tool distribution pie, zone transition history
- Checkpoint results panel: which sessions passed/failed and why
- Alarm history: all alarms with severity and actions
- AGILE board: 6 tasks, all in Done or Review, estimate vs. actual visible on every card
- "The harness governed every one of these sessions without the agent ever knowing about budgets."

---

## Demo Preparation Checklist

- [ ] Scaffold the `snip` project repo with bare `cli.py`, `store.py`, `pyproject.toml`
- [ ] Pre-configure `guardrails.yaml` with demo-friendly defaults (200K daily, 50K session)
- [ ] Set up notification channel (macOS notification for simplicity)
- [ ] Prepare the "budget clamp" demo by having a lowered daily cap ready
- [ ] Prepare the "midnight reset" demo with a script that resets the counter instantly
- [ ] Have direct provider control-plane settings configured for the provider you will demo: provider/model in `.htb/config.toml`, and `AGILE_AI_HTB_CONTROL_API_KEY` in `.htb/secrets.env`
- [ ] Test T1 (save) and T3 (list) end-to-end — these are the core demo beats
- [ ] Have a second browser tab open showing the raw system prompts at each zone (for the yellow/red demo)

---

## Bundle C operator proof: guarded Worker launch

Current guarded launch path: a task can move from **Estimated** to **Running** only after Launch Guardrails pass for the selected Worker Adapter:

- adapter exists and is configured
- adapter verification proves a budget-authoritative tracking mode: `proxy_governed` or trustworthy `native_usage`
- a project is connected and its root exists
- selected model is supported by the adapter
- harness proxy URL and per-session bearer key are available when the verified mode is `proxy_governed`
- `observed_only` diagnostics are not launchable from the normal AGILE Board

The launch endpoint is operator-protected:

```bash
uv run htb init
# Edit .htb/secrets.env once; htb serve/check load it automatically
uv run htb serve
set -a
source .htb/secrets.env
set +a
uv run htb check
# Open http://127.0.0.1:8000
```

1. Connect the target project in the Portal **Projects** flow, then configure the locally available adapter in **Settings → Worker adapters**. Direct SQLite editing is only for local operator recovery. Example for Codex:

   ```bash
   sqlite3 data/harness.db <<'SQL'
   update worker_adapters
      set config_json = '{"command":"codex"}',
          supported_models_json = '["gpt-5.1-codex"]',
          is_default = 1,
          updated_at = datetime('now')
    where id = 'codex';
   SQL
   ```

2. Run adapter verification through the harness. For `proxy_governed`, verification must produce the
   `AGILE_AI_HTB_ADAPTER_OK` sentinel and an `adapter_verification` token row through the Harness Proxy. For `native_usage`, verification must parse trustworthy machine-readable usage evidence from the local CLI with selected model, prompt tokens, completion tokens, total tokens, successful exit status, and run/session binding. Use
   **Settings → Worker adapters → Verify** in the portal, or call the protected API
   directly with the same values:

   ```bash
   curl -sS -X POST http://127.0.0.1:8000/settings/workers/codex/verify \
     -H "Authorization: Bearer $TOKEN_TRACKER_PORTAL_TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"model":"gpt-5.1-codex","proxy_url":"http://127.0.0.1:8000/v1"}'
   ```

3. Create or choose an Estimated task whose recommended model matches the adapter:

   ```bash
   TASK_ID=$(curl -sS -X POST http://127.0.0.1:8000/tasks \
     -H 'Content-Type: application/json' \
     -d '{"description":"Implement snip save","estimate_tokens":8000,"recommended_model":"gpt-5.1-codex"}' \
     | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
   ```

4. Launch through the guarded endpoint or the board's **Launch task** button. The
   default harness proxy URL is `http://127.0.0.1:8000/v1` when omitted. If launching
   a manually sized task, include both `estimate_tokens` and `model`; the endpoint
   persists that manual estimate before evaluating guardrails. Launch is server-gated
   to tasks in **Estimated** state after any manual estimate is applied.

   ```bash
   curl -sS -X POST "http://127.0.0.1:8000/tasks/$TASK_ID/launch" \
     -H "Authorization: Bearer $TOKEN_TRACKER_PORTAL_TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"adapter_id":"codex","model":"gpt-5.1-codex","proxy_url":"http://127.0.0.1:8000/v1"}'
   ```

   Manual-estimate launch example:

   ```bash
   curl -sS -X POST "http://127.0.0.1:8000/tasks/$TASK_ID/launch" \
     -H "Authorization: Bearer $TOKEN_TRACKER_PORTAL_TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"adapter_id":"codex","model":"gpt-5.1-codex","estimate_tokens":8000}'
   ```

5. Confirm the task is **Running**, has a `session_id`, and the board shows a
   **Session report** link. Confirm Worker tokens are recorded after the adapter calls
   the harness proxy with its injected session bearer token:

   ```bash
   sqlite3 data/harness.db "select usage_kind, model, total_tokens from token_turns order by id desc limit 5;"
   ```

   For a completed/failed Worker session, use the board **Refresh status** action or
   `POST /tasks/$TASK_ID/refresh` with the portal bearer token to map completed
   sessions to **Done**/**Review** and failed/aborted sessions to **Blocked**.

Expected proof row for a real Worker launch: `usage_kind = task_execution` for the launched
session/model, with `raw_usage_json.spend_category = worker_execution` and `raw_usage_json.usage_source` set to `harness_proxy` or `native_usage`. The launch response, board, task metadata, and session report must not
contain raw `sk_sess_...` keys; only the session key hash is stored.

Live-proof status for this implementation pass: automated tests do not require real Claude/Codex/OpenCode CLI authentication. The TDD suite uses injected fake runners and the synthetic `demo_worker` path to prove guarded launch, Worker-token session reports, native-usage reconciliation, and observed-only blocking without making provider calls. A local operator with authenticated adapter CLI access should run the optional OpenCode native proof in `docs/GPT-5.4-MINI-LOCAL-DEMO.md` to complete live CLI verification.
