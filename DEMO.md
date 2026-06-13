# Demo Scenario: CLI Snippet Manager

A synthetic project that a coding agent builds live under harness governance. The project is a Python CLI tool (`snip`) for managing code snippets — small enough to complete in a demo but with enough surface area for tasks of varying complexity.

## The Project

**`snip`** — a CLI snippet manager. Commands: `snip save`, `snip list`, `snip search`, `snip delete`. Snippets stored as JSON files in `~/.snip/`. Each snippet has a title, language tag, and body.

**Starting state**: A bare scaffold. `cli.py` has argument parsing via argparse but no commands implemented. `store.py` has a `SnippetStore` class with `__init__` but no methods. `pyproject.toml` exists. No tests, no README.

---

## Demo Tasks

The AGILE board is pre-populated with 6 tasks spanning all three complexity tiers. The demo walks through dispatching them, showing governance at each level.

### Easy tasks

| # | Task | Est. tokens | Complexity | Recommended model |
|---|---|---|---|---|
| T1 | **Implement `snip save`** — accept title, language, and body via CLI args; write snippet to the store | 8K | Simple | Claude Haiku |
| T2 | **Add a `--color` flag** — support `--color/--no-color` for terminal output; pass through to `rich.print` | 5K | Simple | Claude Haiku |

### Medium tasks

| # | Task | Est. tokens | Complexity | Recommended model |
|---|---|---|---|---|
| T3 | **Implement `snip list` with filters** — list all snippets; support `--language` and `--tag` filters; format as a table with `rich` | 25K | Modest | Claude Sonnet |
| T4 | **Add fuzzy search via `snip search`** — accept a query string; use `thefuzz` for fuzzy matching on title and body; rank and display results | 35K | Modest | Claude Sonnet |

### Complex tasks

| # | Task | Est. tokens | Complexity | Recommended model |
|---|---|---|---|---|
| T5 | **Add SQLite backend with migration** — replace JSON file store with SQLite via `sqlite3`; write a migration that imports existing JSON snippets; add `--db-path` flag | 90K | Complex | Claude Opus |
| T6 | **Add `snip share` with gist integration** — accept a snippet ID; push to GitHub Gist via the GitHub API; require a `GITHUB_TOKEN` env var; return the gist URL | 80K | Complex | Claude Opus |

---

## Demo Flow

The presenter walks through the harness as the agent works through the tasks. Each beat shows a specific harness capability.

### Beat 0: Setup (30 seconds)

- Show the harness startup: `docker compose up`
- Portal at `http://localhost:8000` — dashboard empty, 0 sessions
- Show `guardrails.yaml`: daily cap 200K, session cap 50K, zones configured
- AGILE board with all 6 tasks in Backlog column

### Beat 1: Estimation & Model Routing (60 seconds)

- Drag T1 ("Implement `snip save`") to Estimated
- Portal calls `/estimate` — harness classifies as **simple**, recommends **Claude Haiku**, estimates **8K tokens**
- Show the model dropdown pre-selected to Haiku
- Drag T5 ("SQLite backend") to Estimated — harness classifies as **complex**, recommends **Claude Opus**, estimates **90K tokens**
- **Budget clamp demo**: artifically lower daily budget to 50K, then estimate T5 again. Harness warns: "Estimated 90K exceeds remaining 50K daily budget." Model recommendation auto-downgrades: "Budget is tight — downgraded from Opus to Sonnet."
- Show the budget bar: "0 / 200,000 daily tokens (resets in 7h 15m)"

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
- [ ] Have LiteLLM configured with API keys for both Anthropic and OpenAI
- [ ] Test T1 (save) and T3 (list) end-to-end — these are the core demo beats
- [ ] Have a second browser tab open showing the raw system prompts at each zone (for the yellow/red demo)
