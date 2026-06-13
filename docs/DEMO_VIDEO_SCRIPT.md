# AGILE-AI-HTB — Demo Video Script

**Duration:** ~6 minutes
**Setup:** Portal at localhost:8000, pre-seeded with 6 DEMO tasks, one verified worker adapter, `PROVIDER_API_KEY` set.

---

## Part 0: Title Card (10 seconds)

**Show:** Portal login page with AGILE-AI-HTB branding.

**Say:** "AGILE-AI-HTB is a token-budget governance harness for AI coding agents. It sits between your agent and the LLM provider, tracking every token, enforcing budget guardrails, and escalating to a human — not the agent — when things go wrong."

---

## Part 1: The Problem & Four Pillars (45 seconds)

**Show:** Split screen — left: architecture diagram from `docs/HARNESS.md`, right: portal dashboard.

**Say:** "When you give an AI agent a coding task, it burns tokens. How many? On what? Is it stuck in a loop? Did it blow past your daily budget? You don't know — because there's nothing between the agent and the provider counting and constraining.

AGILE-AI-HTB solves this with four pillars.

**Pillar 1: Guardrails.** Six declared constraints. Daily token cap, session cap, budget zones — green, yellow, red — with graduated enforcement. Loop detection, session timeout, tool category limits. All enforced at the transport level. The agent can't ignore them because it doesn't see the real provider — the harness is the provider."

**Show:** guardrails.yaml open in editor, scroll through G1-G6.

**Say:** "**Pillar 2: Checkpoints.** Four pass/fail evaluations that run at session boundaries. Budget health, stuck-loop score, tool diversity, timeout respect. Stateless — you can replay them from any session artifact without re-running the agent."

**Show:** Session report page with checkpoint results table.

**Say:** "**Pillar 3: Material Handling.** Clean interfaces. Tasks come in through the AGILE board. Sessions dispatch to the worker. Reports come back to the portal. The harness never modifies the agent's output — it just counts, constrains, and reports."

**Show:** AGILE board with columns: Estimated → Ready → Running → Review → Done → Blocked.

**Say:** "**Pillar 4: Alarms.** Seven named alarm types with severity and recommended actions. Budget yellow, budget red, daily cap exceeded, loop detected, session timeout, tool category bias, checkpoint fail. Every alarm escalates to a human decision — continue, abort, or adjust."

**Show:** Alarm log from a completed session.

---

## Part 2: Live Demo — The Full Loop (3 minutes)

### Beat 1: Estimate a task (45 seconds)

**Show:** Portal board page. Point at the intake form.

**Say:** "Here's the AGILE board. Six columns representing the full lifecycle. Let's walk through the loop with a real task."

**Action:** Type "Add a save command to the CLI snippet manager" into the intake form. Click "Estimate task."

**Say:** "I type a task description and click Estimate. The harness calls its own Estimator LLM — not my agent, the harness's own model. It returns a structured estimate: token budget, complexity, recommended model, confidence, assumptions, risk flags. The estimator's tokens are tracked as orchestration spend, separate from worker tokens."

**Show:** Card appears in Estimated column with token estimate, model, confidence.

**Say:** "The task lands in Estimated with metadata from the estimator. Notice it says 'Configure Worker Adapter to launch' — that's a Launch Guardrail. The harness won't let me launch until it can prove it can track the worker's tokens."

### Beat 2: Configure and verify worker adapter (30 seconds)

**Show:** Navigate to `/settings/workers`.

**Say:** "Worker Setup shows my available adapters. I've got a demo worker pre-configured and verified. The harness has already proven it can track this worker's token traffic through the proxy."

**Show:** Worker card with verified badge.

**Say:** "Back on the board, the Launch button is now visible on my Estimated task."

### Beat 3: Launch and watch governance (60 seconds)

**Show:** Click Launch on the task.

**Say:** "I click Launch. The harness checks all launch guardrails — adapter configured, verified, workdir valid, model supported, proxy wired. All pass. It starts a session, spawns the worker, and the worker begins making API calls through the harness proxy."

**Show:** Navigate to dashboard during session.

**Say:** "The worker is calling the proxy, which forwards to the real LLM provider through LiteLLM. Every request is governed. The harness rewrites the system prompt, clamps max_tokens, and removes blocked tools based on the budget zone. The worker doesn't know any of this is happening — it just sees the proxy as its API endpoint."

**Show:** Session report as it builds.

**Say:** "Token turns are accumulating. Let's look at the session report."

### Beat 4: Session report and checkpoints (45 seconds)

**Show:** Session report page after session completes.

**Say:** "Session complete. Here's the report. Token totals — prompt, completion, total. Tool breakdown — what the worker used and how many calls. Current zone — green, since we stayed well under budget. Alarms — none fired because everything was clean. Checkpoints — all four passed.

Every one of these token turns went through real LLM calls. The estimator used a real model. The worker used a real model. The harness counted every token, applied governance on every request, and produced this report without the worker ever being aware of budgets."

---

## Part 3: Architecture & Deploy (45 seconds)

**Show:** Architecture diagram.

**Say:** "Under the hood: FastAPI, SQLite, LiteLLM, Jinja2 templates. Single Docker container. Agent-agnostic — any OpenAI-compatible agent works. LiteLLM normalizes over 100 providers."

**Show:** `docker compose up` output.

**Say:** "Deploy anywhere Docker runs. We've got a render.yaml Blueprint for one-click Render deploys with a persistent disk for SQLite."

**Show:** `render.yaml` and Render dashboard.

**Say:** "Set two secrets — portal token and provider API key — and you're live."

---

## Part 4: Human-in-the-Loop (30 seconds)

**Show:** Alarm escalation decision panel.

**Say:** "The most important principle: the harness constrains the agent, never the human. When a budget cap is exceeded, when a loop is detected, when a checkpoint fails — the harness surfaces the decision to you. Recommended action, context, one click to continue, abort, or adjust.

The agent doesn't get to decide. You do."

---

## Part 5: Outro (15 seconds)

**Show:** Portal dashboard with completed session stats.

**Say:** "AGILE-AI-HTB. Token-budget governance for AI coding agents. Open source. Deploy in minutes. Your budget, your rules, your decisions."

---

## Recording Checklist

- [ ] Portal running locally: `docker compose up`
- [ ] `PROVIDER_API_KEY` set in environment
- [ ] Demo tasks seeded: `htb seed-demo`
- [ ] One verified worker adapter configured
- [ ] Screenshot / recording tool ready (QuickTime, OBS, or CleanShot)
- [ ] Browser at 1280x720, no bookmarks bar, dark theme
- [ ] Terminal ready for architecture shots
- [ ] guardrails.yaml open in separate tab
- [ ] Record in 1080p, 30fps
- [ ] Test the full loop once before recording
