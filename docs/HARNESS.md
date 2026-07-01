# AGILE-AI-HTB

AGILE-AI-HTB is a token-tracker harness that governs AI coding agents through **declared guardrails**, **structured checkpoints**, **clean material handling**, and **named alarms** — all operating in the domain of token-budget governance.

## Architecture Overview

AGILE-AI-HTB uses a deployable control-plane / execution-plane architecture. The hosted Harness can coordinate work, govern budgets, expose the Portal, proxy model traffic, and track tokens, but actual repository access and coding-agent launch happen through a pluggable **Execution Backend**. The first launch-capable backend is a **Local Runner** running near the user's repo; a **Hosted Workspace/Sandbox** is the later cloud-native path; analysis-only Git workspaces are useful immediately for task breakdown and estimation but are not launch-ready until an execution backend is verified.

```
┌─────────────────────────────────────────────────────────────┐
│                        HARNESS                              │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐ │
│  │GUARDRAILS│   │CHECKPOINTS│   │ ALARMS   │   │MATERIAL │ │
│  │          │   │          │   │          │   │HANDLING │ │
│  │ Budgets  │   │ Health   │   │ Budget   │   │ Portal  │ │
│  │ Zones    │   │ Patterns │   │ Loops    │   │ API     │ │
│  │ Limits   │   │ Scores   │   │ Timeouts │   │ Board   │ │
│  └─────┬────┘   └────┬─────┘   └────┬─────┘   └────┬────┘ │
│        │             │              │              │       │
│  ┌─────┴─────────────┴──────────────┴──────────────┴─────┐ │
│  │                   PROXY ENGINE                         │ │
│  │   Intercepts LLM API calls → counts tokens             │ │
│  │   Evaluates guardrails per turn → injects context      │ │
│  │   Records tool calls → feeds analytics                 │ │
│  └────────────────────────┬──────────────────────────────┘ │
│                           │                                │
│  ┌────────────────────────┴──────────────────────────────┐ │
│  │               SESSION ARTIFACT STORE                   │ │
│  │   SQLite: token logs, tool traces, alarm history,      │ │
│  │   checkpoint results, guardrail state snapshots        │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │                                │
    ┌────┴────┐                      ┌────┴────┐
    │  AGENT   │                      │  USER   │
    │ (Hermes, │                      │ Portal  │
    │  Claude, │                      │   UI    │
    │  Codex)  │                      └─────────┘
    └─────────┘
```

**Control Plane design**: The deployable harness runs as one FastAPI application serving three roles:

1. **LLM Proxy** — The agent points its `OPENAI_BASE_URL` (or equivalent) at the harness. All API calls arrive at the harness, which uses explicit direct provider clients to forward to the configured upstream provider. OpenAI and OpenAI-compatible providers use `/v1/chat/completions`; Anthropic requests are translated to the Messages API and normalized back to OpenAI-shaped responses. Governance layers (system prompt rewrite, max_tokens clamping, tool restriction) are injected into the request before forwarding.
2. **REST API** — Session management (`/session/start`, `/session/{id}/report`), guardrail CRUD, checkpoint evaluation, alarm history.
3. **Portal UI** — HTML served via HTMX + Jinja2. Dashboard with token charts, AGILE task board, session history, alarm log.

**Deployment**: The Control Plane can deploy as a single Docker container. SQLite backs the artifact store for the initial demo. Local launch against a user's private/local repo requires a paired Local Runner; a hosted deployment cannot directly access a laptop filesystem. Git URL projects may be analysis-ready in the hosted Control Plane before they are launch-ready.

### Control plane and execution backends

The Harness separates coordination from execution:

| Concept | Responsibility | First target |
|---|---|---|
| **Control Plane** | Portal, AGILE Board, budgets, Task Breakdown Agent, Estimator LLM, Proxy Engine, token accounting, reports | Local Docker/FastAPI app; hosted target stays platform-neutral |
| **Local Runner** | Runs near the user's local repo, launches local Claude Code/Codex/OpenCode/Hermes adapters, sends model traffic through the Harness proxy | Built into all-in-one local mode first; split/tunnel runner later |
| **Hosted Workspace/Sandbox** | Clones Git repos for hosted analysis and later cloud-side Worker execution | Future launch backend; analysis-only first |
| **Analysis-only backend** | Allows task breakdown and estimation without Worker launch | Available for hosted Git URL workspaces |

Project capability is explicit in the Portal:

- **Not connected** — no project context.
- **Analysis-ready** — enough context for Task Breakdown and Task Estimation, but no verified execution backend.
- **Launch-ready via Local Runner** — runner is online, paired, has repo access, and Worker Adapter verification passed.
- **Launch-ready via Hosted Workspace/Sandbox** — hosted execution environment is sandboxed, configured, and verified.
- **Blocked** — project exists but no execution backend satisfies Launch Guardrails.

This prevents the hosted product from claiming it can run a user's local coding agent when no local execution bridge exists.

The minimum scale proof is one Control Plane coordinating multiple project/backend states, not every backend being fully launchable. The demo should show at least:

- one project **Launch-ready via Local Runner** with OpenCode verified end-to-end;
- one project **Analysis-ready** through a Git/Hosted Workspace profile where breakdown and estimation work but launch is disabled;
- one project or adapter **Blocked** because Launch Guardrails lack a verified execution backend.

This proves the Control Plane can govern heterogeneous execution readiness at scale while keeping launch claims truthful.

The first implementation slice is the **local execution slice**. It must prove real governance before expanding the dashboard: `htb init`, `htb serve`, configure/test the control-plane connection through `/settings/control-plane` or ignored local secret storage, `htb check`, connect a local repo path, detect OpenCode, verify the real OpenCode CLI launch path, record `adapter_verification` tokens through a budget-authoritative tracking mode, mark the project **Launch-ready via Local Runner**, launch one tiny task through OpenCode, and prove Worker tokens hit the Harness ledger. The first launch proof should be read-only: OpenCode inspects the connected repo and writes a short session report artifact summarizing language, test command, and top-level structure. After that passes, a second proof may perform a tiny docs-only codebase change.

Launch Guardrails distinguish read-only from write-capable sessions. Read-only repo inspection may run even when the connected repository has uncommitted changes. Write-capable sessions require a detected git repository, visible current branch, and clean working tree before launch so Worker changes do not mix with pre-existing user edits. After the clean-tree check passes, the runner creates a task branch such as `htb/task-123-short-title`, launches the Worker on that branch, and records the branch name in the Session Artifact and Portal review flow. The Worker may edit files on the task branch, but the Harness owns final git history: after configured verification passes, the Harness creates the commit with task/session metadata. Commit gating uses the Project Profile test command plus a Harness-generated git diff review summary. If no test command is configured, verification is marked "missing test command" and manual approval is required before commit. If verification fails, changes remain uncommitted for review or retry. Pull request creation is optional, not required for the first local execution slice: when a GitHub remote and authenticated `gh` CLI are available, the Portal may show an Open PR action after the Harness-Owned Commit exists.

Worker failure handling separates operational launch failures from hard blockers. If OpenCode crashes, exits non-zero, times out, or produces no budget-authoritative usage after a launchable Task has started, the Worker Run fails, the Task returns to **Estimated**, and the Harness preserves sanitized launch-error evidence for retry. Hard safety/workflow failures, such as read-only project mutation or write-capable verification failure requiring manual intervention, move or keep the Task **Blocked** with preserved logs, token ledger entries when present, failure reason, branch name, and any uncommitted diff.

Project boards support bounded Level 1-3 run automation. `/projects/{project_id}/board` shows a compact Run automation panel with live refresh, `Run next task`, and an explicit one-at-a-time `Run queue`. The queue uses the same Task Launch path and Launch Guardrails as manual launches, records automation policy/source/stop evidence, and stops on no eligible Tasks, operator stop, guardrail failure, budget override requirement, native usage acknowledgement requirement, retryable Worker failure, or hard blocker. Auto Agent Review may be enabled for queued successful Worker Runs, but it only stores advisory review evidence; the operator still chooses Mark Done or Block. There is no cross-project autopilot, auto-budget override, auto-Done, or autonomous repair loop.

### Local run modes

The first local implementation should be **all-in-one local mode**:

```bash
htb init
htb serve
htb check
```

In this mode, the Control Plane and Local Runner run on the same machine and may share one process. The Portal connects a local repo path, validates the Project Profile, detects Worker Adapters, verifies launch capability, and launches Workers in that repo. A Worker Adapter is a local coding-agent CLI integration; Harness Proxy routing is one tracking mode, not the definition of the adapter.

Local execution smoke path:

```bash
# Start the all-in-one Control Plane + Local Runner
htb init
# Add/test the control-plane key in /settings/control-plane after the portal starts.
# Ignored .htb/secrets.env and shell env values remain supported alternatives.
htb serve
htb check

# In another shell, run the reproducible synthetic smoke.
# It requires OpenCode on PATH, initializes a temporary git repo, connects it
# through LocalExecutionBackend, marks synthetic adapter-verification evidence,
# launches a read-only proof, then runs a write-capable docs-only session with
# budget override and Harness-owned commit verification.
uv run python scripts/local_runner_smoke.py
```

The smoke intentionally does not require provider secrets. It records synthetic `task_execution` token rows through the same SQLite ledger APIs used by the proxy path, so Launch Guardrails still prove that session accounting, budget override metadata, overrun alarms, task branch creation, test-command gating, diff summary capture, and Harness-owned commit persistence all work. For a real Worker Adapter verification, use the Portal Worker Setup flow so OpenCode makes the sentinel model call through `/v1/chat/completions` and the Harness records adapter-verification token usage.

Later modes preserve the same Execution Backend contract:

| Mode | Shape | Purpose |
|---|---|---|
| **All-in-one local** | `htb init` then `htb serve` | First demo/dev path; proves real local repo + local Worker launch |
| **Split local** | `htb serve` plus `htb-runner serve --server http://localhost:8000 --project /path/to/repo` | Tests runner lifecycle and mirrors hosted architecture |
| **Hosted + tunnel** | `htb-runner connect --server https://... --project /path/to/repo --tunnel ngrok|cloudflare` | Deployed Control Plane controlling a local execution backend |

The local-first implementation must keep the code boundary as an `ExecutionBackend` so split runner, tunnel runner, and hosted sandbox can be added without rewriting the AGILE Board.

The first verified local Worker Adapter target is **OpenCode** through native usage import. Claude Code, Codex, and Hermes remain first-class adapter presets in the Portal, but Launch Guardrails keep them non-launchable until adapter verification proves budget-authoritative token tracking. Adapter verification is not an install-only check: it must run a tiny sentinel prompt through the real Worker Adapter CLI and prove token usage through one verified tracking mode. Public README/getting-started docs should describe the verified native-usage path only; `proxy_governed` stays architecture/internal until a stock proxy-capable adapter is proven end-to-end:

- `proxy_governed` — advanced/custom path where Worker model traffic routes through the Harness Proxy with a session-scoped Harness key and records token rows under `adapter_verification` orchestration spend.
- `native_usage` — the Worker CLI emits trustworthy machine-readable native token usage evidence that the Harness records under `adapter_verification` orchestration spend. The evidence must include the selected model, prompt/input tokens, completion/output tokens, total tokens, exit status, and a command/session identifier or equivalent evidence binding usage to the launched Worker Run. Human-readable logs, approximate usage, missing model identity, or usage that cannot be bound to the run is not authoritative and leaves the adapter `observed_only`.
- `observed_only` — the Harness observes process/log evidence only; this is useful for diagnostics but is not launchable for governed Tasks.

Provider API keys live only in the Harness process for `proxy_governed` launches. Workers receive only a session-scoped Harness key and Harness Proxy base URL, for example `OPENAI_BASE_URL=http://127.0.0.1:8000/v1` and `OPENAI_API_KEY=<harness-session-key>`, so Worker Adapters cannot bypass token tracking by calling the provider directly. For `native_usage` launches, the Worker may use its existing local CLI authentication, but Launch Guardrails require trustworthy usage evidence before the adapter is governed-launchable.

**Multi-provider support**: The harness keeps a stable OpenAI-compatible proxy endpoint for Workers while using explicit upstream provider clients. Configure `AGILE_AI_HTB_CONTROL_PROVIDER` as `openai`, `openai-compatible`, or `anthropic`; set `AGILE_AI_HTB_CONTROL_BASE_URL` for OpenAI-compatible providers that are not OpenAI. Adding a new upstream provider is a small explicit client change, not a hidden universal abstraction.

### Direct Provider Integration

Direct provider clients are the transport layer. The harness owns all governance logic and runs it *before* forwarding the request upstream.

**What the direct provider layer provides:**

| Capability | Implementation | Notes |
|---|---|---|
| Provider selection | `AGILE_AI_HTB_CONTROL_PROVIDER` | Explicit: `openai`, `openai-compatible`, or `anthropic` |
| OpenAI-compatible forwarding | `POST {base_url}/chat/completions` | Supports OpenAI and compatible providers with bearer auth |
| Anthropic forwarding | `POST /v1/messages` | Translates system/user/assistant messages and normalizes the response |
| Token counting | Provider `usage` fields | OpenAI `prompt_tokens`/`completion_tokens`; Anthropic `input_tokens`/`output_tokens` |
| Cost calculation | Optional local pricing table | Unknown models store zero dollar cost while preserving tokens |
| Streaming | OpenAI-compatible SSE | Final usage chunk remains authoritative; Anthropic streaming is explicitly rejected until usage-preserving support is added |

**What the harness owns (our code)**:

All governance happens before the upstream provider call. On every turn:

```
# 1. Check zone state (green/yellow/red based on live daily budget)
zone = session.get_zone()

# 2. Rewrite system prompt (Layer 1)
messages = inject_zone_prompt(original_messages, zone)

# 3. Clamp max_tokens (Layer 2)
max_tokens = ZONE_MAX_TOKENS[zone]

# 4. Strip blocked tools (Layer 3)
tools = filter_blocked_tools(original_tools, zone)

# 5. Forward via the configured direct provider client
response = await llm_client.acompletion(
    {
        "model": session.model,
        "messages": messages,
        "max_tokens": max_tokens,
        "tools": tools,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
)

# 6. Extract token counts, store in session artifact
session.record_turn(response.usage.prompt_tokens, response.usage.completion_tokens)

# 7. Fire alarms if thresholds crossed
session.check_alarms()
```

**Streaming token counting caveat**: For streaming OpenAI-compatible calls, use `stream_options={"include_usage": True}` and read token counts exclusively from the final usage chunk. Do not sum across intermediate chunks.

**Cost tracking**: Token counts are authoritative. Dollar cost is optional: the local pricing table can compute known model prices, and unknown models record zero/unknown cost without blocking token tracking.

**Why not provider-native guardrails?** Provider guardrail systems operate outside the exact request transforms this harness needs. Our three-layer governance — system prompt rewriting, `max_tokens` clamping, and tool restriction — modifies the actual LLM request parameters before the upstream provider call.

## Pillar 1: Guardrails

Guardrails are **declared** in `guardrails.yaml`, not buried in code. Each session can override the defaults.

### Enforced guardrails


| #   | Guardrail                          | Declaration                                   | Enforcement                                                                                                             |
| --- | ---------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| G1  | **Daily token cap**                | `daily_cap: 1_000_000` (user-configurable) | Calendar-day reset at midnight local time. Notify when exceeded; sessions continue. Portal shows "resets in Xh Ym." |
| G2  | **Session token cap**              | `session_cap: 200_000`                        | Notify when session exceeds cap; agent continues                                                                        |
| G3  | **Budget consumption zones**       | `zones: {green: 60%, yellow: 85%, red: 100%}` | Three-layer enforcement: system prompt rewrite, max_tokens clamping, tool restriction — graduated per zone |
| G4  | **Loop detection**                 | `loop_threshold: 5`                           | Same tool + same input hash repeated N times → `LOOP_DETECTED` alarm; notify user                                       |
| G5  | **Session timeout**                | `session_timeout: 30m`                        | Wall-clock time exceeded → `SESSION_TIMEOUT` alarm; notify, save checkpoint                                             |
| G6  | **Tool-category budget weighting** | `tool_category_limit: 50%`                    | No single tool category may consume >50% of session budget → `TOOL_CATEGORY_BIAS` alarm; inject warning context         |


### Enforcement model

The harness uses a **three-layer graduated enforcement** model. No layer hard-stops the agent, but each layer constrains behavior more tightly as the budget depletes — the agent *cannot* ignore the constraints.

These are **runtime request guardrails**: they apply after a Session has started only when the Worker is making model calls through the Proxy Engine in `proxy_governed` mode. Budget guardrails are not automatic mid-task kill switches: if a running Worker Session exceeds estimate or budget, the Harness records the overrun, raises alarms, and lets the task finish unless the user/admin manually aborts. Exhausted budget blocks new launches through Launch Guardrails unless the User explicitly approves a budget override. If a Task estimate exceeds remaining budget before launch, the Portal changes the action to **Launch with budget override**, records `budget_override=true`, and audits the approval. For `native_usage`, that approval must include explicit acknowledgement that native usage cannot be request-throttled mid-run and may reconcile as an overrun after completion.

Tracking modes have different governance strength:

| Tracking mode | Accounting authority | Runtime request governance |
|---|---|---|
| `proxy_governed` | Budget-authoritative token rows from the Harness Proxy | Yes: system prompt rewrite, max-token clamping, and request-time restrictions can apply while calls pass through the Proxy Engine |
| `native_usage` | Budget-authoritative only after trustworthy native usage evidence is parsed and bound to the Worker Run | No: governance is launch/review-time only — budget preflight, post-run reconciliation, evidence review, and alarms after usage is known |
| `observed_only` | Not budget-authoritative | No: process/log evidence only and not launchable for governed Tasks |

Budget override behavior follows the same distinction. `proxy_governed` sessions may launch with override approval while runtime request guardrails remain available. `native_usage` sessions may also launch with override approval, but the Portal must warn that the Harness cannot throttle native CLI model requests mid-run; actual usage is reconciled after the run and may exceed the approved estimate. `observed_only` never receives an AGILE Board budget override because it is not launchable from the normal board.

Portal labels should make that distinction explicit:

| Tracking mode | Portal label | Runtime request guardrails | Accounting copy |
|---|---|---|---|
| `proxy_governed` | Governed via Harness Proxy | Available | Budget-authoritative during run |
| `native_usage` | Tracked via Native Usage | Not available | Budget-authoritative after run |
| `observed_only` | Observed Only | Not available | Not budget-authoritative |

The Portal should not collapse these into a generic "Governed" badge. Adapter cards should show launch readiness separately from tracking strength, for example `Status: Launch-ready`, `Tracking: Tracked via Native Usage`, `Runtime request guardrails: Not available`, and `Accounting: Budget-authoritative after run`.

`observed_only` is never launchable from the normal AGILE Board because that board is the product promise surface for governed token tracking. Worker Setup may expose a separate **Test adapter** or **Run diagnostic prompt** action for observed-only adapters. That diagnostic action records command start evidence, stdout/stderr, exit code or timeout, detected model when available, and a clear **not budget-authoritative** warning. It must not change task state, show a Launch-ready badge, or present the run as a governed Worker Session.

### Launch guardrails

Launch guardrails run before a Task can move from **Estimated** to **Running** on the AGILE Board. They protect the product promise: if the harness cannot govern and observe the Worker, the portal must not present that work as tracked or governed.

| Launch guardrail | Requirement | Failure behavior |
|---|---|---|
| Worker Adapter configured | User selected and configured Claude Code, Codex, OpenCode, Hermes, or another supported adapter | Launch is guardrail-blocked |
| Token tracking verified | A setup test proves the adapter has a budget-authoritative tracking mode: `proxy_governed` token rows through `/v1/chat/completions` or trustworthy `native_usage` evidence from the CLI | Launch is guardrail-blocked |
| Session key wiring present | Required only for `proxy_governed` adapters so the adapter can receive the harness URL and session-scoped API key | Launch is guardrail-blocked for proxy-governed launches |
| Working directory valid | Adapter can start in the selected project directory | Task remains Estimated or Blocked |
| Model allowed | Selected/recommended model is allowed by config and compatible with the adapter | User must pick another model or adjust config |

The setup test is intentionally synthetic but must exercise the real adapter launch path: the harness creates a small disposable Session, launches the configured Worker Adapter with one harmless prompt, then checks that `prompt_tokens`, `completion_tokens`, and `total_tokens` were recorded from the verified tracking mode. A direct proxy call is not enough; the point is to prove Claude Code, Codex, OpenCode, Hermes, or the custom command is actually launchable under Harness observation. If no budget-authoritative usage appears, the adapter is **not launchable** from the AGILE Board for governed Tasks.

Adapter verification prompt:

```text
You are running an AGILE-AI-HTB adapter verification. Reply with exactly:
AGILE_AI_HTB_ADAPTER_OK
Do not inspect files. Do not run tools. Do not modify anything.
```

Adapter verification passes only when the adapter process exits successfully, the response contains the exact sentinel `AGILE_AI_HTB_ADAPTER_OK`, token usage is persisted for the disposable Session, the persisted model matches the selected/configured model, and no tool traces or file writes occurred. Verification tokens count against the daily budget as orchestration tokens labeled `adapter_verification`; they do not count as Task actuals and should be hidden from the normal task board or marked as system verification.

Worker Adapter setup lives in Settings as the source of truth. The AGILE Board only displays the selected adapter status and launch readiness:

- `/settings/workers` configures adapters, runs verification, shows launchable status, and chooses the default Worker Adapter.
- Task cards show the default Worker Adapter, allow a per-task override to another launchable adapter, and show whether token tracking is verified.
- If an adapter is not launchable, the AGILE Board keeps Launch visible but returns explicit guardrail failure copy and links to Worker Setup.
- If an adapter loses verification before Launch, the Task remains Estimated or Blocked until the User picks a launchable adapter.

#### Layer 1: Progressive system prompt rewrites

At each zone transition, the harness rewrites the agent's entire system prompt with progressively tighter instructions:

| Zone | System prompt instruction |
|---|---|
| Green | "You have ample token budget. Be thorough: write tests, add documentation, explore alternatives." |
| Yellow | "Budget is limited. Prioritize the core task. Skip documentation and non-essential tests. Be concise." |
| Red | "Budget critical. Output only the final deliverable. No explanations, no exploration, no tests. If you cannot finish in two turns, deliver what you have." |

#### Layer 2: Zone-based `max_tokens` limiting

The harness sets the `max_tokens` parameter on every API call based on the current zone. The agent physically cannot produce long responses in constrained zones:

| Zone | max_tokens |
|---|---|
| Green | Full (configurable, default 4096) |
| Yellow | 50% of green (2048) |
| Red | 25% of green (1024) |

#### Layer 3: Zone-based tool restrictions

The harness modifies the available `tools` list in the API call. In constrained zones, expensive or exploratory tools are removed:

| Zone | Available tools |
|---|---|
| Green | All tools |
| Yellow | Remove `web_search`, `browser_*` (expensive exploration) |
| Red | Only `read_file`, `patch`, `terminal` (delivery-only tools) |

The agent cannot search the web, browse, or delegate in red zone — those tools don't exist in the API call.

#### Alarms (always active)

In addition to the three enforcement layers, every guardrail also produces **alarm notifications**: structured alarms fired to the user via configured notification channel for visibility, even when the harness is automatically constraining the agent.

### Declaration format

```yaml
# guardrails.yaml
daily_cap: 1000000
session_cap: 200000
zones:
  green: 0.60   # 0-60%: normal operation
  yellow: 0.85  # 60-85%: context injection, wrap-up signal
  red: 1.0      # 85-100%: alarm fires
loop_threshold: 5
session_timeout: 1800  # seconds
tool_category_limit: 0.50
```

Per-session overrides are passed as JSON in the `/session/start` payload.

## Pillar 2: Checkpoints

Checkpoints evaluate agent output at **session boundaries** using explicit pass/fail criteria. They read from the session artifact (token log, tool trace, guardrail state) — the agent itself is not evaluated directly.

### Checkpoint types


| #   | Checkpoint           | Pass criteria                                               | Evaluates                                                             |
| --- | -------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------- |
| C1  | **Budget health**    | Session consumed ≤ remaining daily budget * fairness factor | Was this session's spend proportional to work remaining?              |
| C2  | **Stuck-loop score** | Loop alarms fired < 3 during session                        | Did the agent get stuck in repetitive behavior?                       |
| C3  | **Tool diversity**   | Agent used ≥ 3 distinct tool categories                     | Was the agent's tool usage well-rounded, or did it rely on one thing? |
| C4  | **Timeout respect**  | Session ended before timeout (natural completion)           | Did the agent finish its work before the clock ran out?               |


### Persistence & replay

Every session produces a JSON artifact:

```
session_artifacts/
  {session_id}/
    token_log.json      # Every API call: timestamp, model, prompt_tokens, completion_tokens
    tool_trace.json     # Every tool invocation: name, input_hash, timestamp, duration
    alarms.json         # All alarms fired during session
    guardrail_snapshots.json  # Guardrail state at each turn boundary
    checkpoint_results.json   # Pass/fail + details for each checkpoint
    output_summary.json       # Agent's final result
```

The checkpoint evaluator is a **stateless function**: `evaluate(session_artifact) → CheckpointResult[]`. To replay from any checkpoint, load the artifact and re-run the evaluator — no agent re-execution needed.

## Pillar 3: Material Handling

Clean interfaces for passing material between the **user**, the **harness**, and the **agent**.

### Interfaces


| Interface               | Direction       | Transport                    | Description                                                                                          |
| ----------------------- | --------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Task submission**     | User → Harness  | Portal (AGILE Board)         | User creates task with description, token estimate. Board shows budget impact before dispatch.       |
| **Session dispatch**    | Harness → Agent | Proxy (API call forwarding)  | Harness starts agent with guardrail config, budget zone, and task context injected as system prompt. |
| **Token analytics**     | Harness → User  | Portal (Dashboard)           | Charts: token burn over time, tool usage distribution, budget zone timeline, session history.        |
| **Session report**      | Harness → User  | Portal + REST API            | Per-session: token totals, tool call breakdown, alarms fired, checkpoint results, agent output.      |
| **Guardrail config**    | User → Harness  | `guardrails.yaml` + REST API | Declare defaults; override per session.                                                              |
| **Alarm notifications** | Harness → User  | Webhook / OS notification    | Push alarms to configured channel (Discord, Slack, macOS notification).                              |


### AGILE Board

The AGILE Board is the user-facing Kanban-style orchestration surface for coding work, not a full Scrum/Jira replacement. Canonical columns are **Estimated → Running → Review → Done**, with **Blocked** for failed estimation or tasks that need human changes before launch or continuation. There is no normal unestimated Backlog because task intake exists to break down, estimate, and budget token spend. Each task card shows:
- Task description
- Estimated token budget (user-overridable)
- Recommended model (task-complexity driven, user-overridable)
- Selected Worker Adapter (Claude Code, Codex, OpenCode, Hermes, or custom)
- Per-task Worker Adapter override when the default is not desired
- Launch guardrail status, especially whether token tracking has been verified
- Actual token cost + estimate vs. actual delta (populated on completion)
- Session link

**Task intake**: The primary task form is labeled **Estimate task**, not **Create task**. Submitting work does not immediately create a board card. Markdown uploads, Markdown paste, and clearly oversized plain text first go through a harness-owned **Task Breakdown Agent**; short plain-text tasks may go directly to Task Estimation. The Task Breakdown Agent reads the input semantically and decides whether the work is a single Task or should be separated into multiple smaller Tasks; it is not a simple character-count or bullet-count classifier. The Task Breakdown Agent may use lightweight project context such as language, framework, test command, top-level folders, README, CONTEXT.md, and HARNESS docs, but it does not inspect arbitrary source files during normal breakdown. If deeper code inspection is needed, it should recommend a Spike rather than silently performing implementation discovery. Markdown is always review-first: even a single-task Markdown decision shows a **Proposed Task Breakdown** review screen before board cards are created. Task breakdown follows tracer-bullet vertical-slice rules: proposed tasks should be independently grabbable, narrow, demoable or verifiable on their own, dependency-aware, and should cut through the needed product layers rather than splitting work by schema/API/UI/test layer. Each proposed task shows title, implementation prompt, acceptance criteria, blockers, HITL/AFK category, and the agent's reason for splitting. The User can accept, reject, or edit proposed tasks. Stage 2 runs Task Estimation only for accepted breakdown items or short plain-text tasks; only then do Tasks appear in Estimated with official token estimate, model recommendation, rationale, confidence, risks, and Spike recommendation. Task Breakdown Agent spend counts against the daily budget as **orchestration tokens** labeled `task_breakdown`. Estimation spend is separately labeled `estimation`. On estimator failure, the affected Task appears in Blocked with manual estimate/model entry.

**Token estimation (LLM-assisted)**: User types a task description. The harness calls a harness-owned **Estimator LLM** with the task, lightweight project context (language/framework summary, test command, relevant file/path hints if supplied), current budget context, and model-routing policy. It does not use the User's Worker Adapter and does not full-scan the repository for every estimate. The Estimator LLM returns structured output: token estimate, complexity, recommended model, confidence, rationale, assumptions, risk flags, and whether a spike is needed because the estimate is low-confidence. The result is displayed on the task card; user can override estimate or model before launch. Estimator LLM spend counts against the daily budget as **orchestration tokens**, but is labeled separately from Worker Session tokens.

**Spike workflow**: If estimation confidence is low, or if the User chooses it, the board can launch a Spike before implementation. A Spike is a Worker Session, so it requires a launchable Worker Adapter with token tracking already verified. It is bounded by purpose: allowed to inspect files, inspect configuration, and run targeted non-mutating tests or discovery commands, but not allowed to edit production code, run destructive commands, run broad test suites without approval, run migrations, or commit. It has no spike-specific token cap; normal daily and session guardrails still apply. By default it uses the same Worker Adapter and model intended for implementation; the User may override to a cheaper or faster launchable adapter/model. Its prompt explicitly forbids edits and commits. Its output is findings, revised estimate, risks, and launch recommendation. Spike tokens count against the daily budget as orchestration tokens labeled `spike`, but do not count as Task actual implementation tokens. After the Spike, the harness automatically updates the Task estimate, recommended model, confidence, rationale, and risks; the Task returns to Estimated with an `updated by spike` badge. The User still accepts the estimate and chooses the Worker before Launch.

If the Estimator LLM is unavailable or returns invalid output, the board offers manual estimate + model entry and clearly marks the task as **manual estimate, not LLM-estimated**. The harness must not silently fall back to a fake heuristic estimate. Manual estimates are launchable once the User enters the required token estimate and model and all launch guardrails pass.

**Model recommendation (task-complexity matching)**: During estimation, the harness classifies the task's complexity — simple, modest, or complex — and recommends a model tier. It does not choose the Worker Adapter:
- **Simple** (e.g., center a div, fix a typo) → Haiku / GPT-4o-mini
- **Modest** (e.g., add an API endpoint, write unit tests) → Sonnet / GPT-4o
- **Complex** (e.g., refactor auth, design a new feature) → Opus / GPT-4.5

The recommendation is pre-selected in a model dropdown; user can override. The selected Worker Adapter is checked for compatibility with that model before launch. The harness also applies a **budget-aware clamp**: if remaining daily budget is below a threshold, it downgrades the recommendation one tier (complex → modest, modest → simple) and shows a note: "Budget is tight — downgraded from Sonnet to Haiku."

**Direct dispatch**: One task → one session → one budget. "Launch" starts a session from the Estimated column after the User accepted or entered the estimate, selected a Worker Adapter, selected or accepted a model, and all launch guardrails passed. No queuing, no batching — cleanest mental model for analytics.

**Pre-dispatch budget check**: Before dispatch, the board checks whether the task's estimated tokens exceed the remaining daily budget. If they do, a warning banner appears ("⚠️ This task's estimate (200K) exceeds remaining daily budget (100K). The DAILY_CAP_EXCEEDED alarm will fire during this session.") but the user can still dispatch — consistent with soft-enforcement across all guardrails.

**Session completion lifecycle**:
- Clean completion → card lands in **Done** with green badge, estimate vs. actual delta, and model used
- Checkpoint failure or alarm fired → card lands in **Review** with red badge; human must review session report and manually advance to Done

**Global budget bar** at top: "800,000 / 1,000,000 daily tokens (resets in 4h 32m)." Shows consumption across all sessions today. When estimating a new task, the bar previews the post-estimate utilization.

**Midnight reset during active sessions**: The zone state is always relative to the live daily budget, not locked at session start. If a session is in yellow or red zone and the clock hits midnight, the daily budget resets to zero consumption, the session returns to green zone, and the agent regains full tools and max_tokens. No session restart needed — the proxy re-evaluates zone on every request. The portal shows a notification: "Daily budget reset. Session returned to green zone." This proves the harness is stateful and responsive, not a one-time config check.

**Second-worker swap (bonus)**: Completed task cards in the Done column include a "Re-run with..." action. User picks a different model, and the same task is re-dispatched to a new agent — zero harness changes. Portal shows both sessions side-by-side for comparison. This proves agent portability: the harness governs whichever agent is plugged in.

### REST API surface

```
POST   /session/start          ← Start a new agent session with guardrail overrides
GET    /session/{id}/report    ← Full session analytics
GET    /session/{id}/artifact  ← Raw JSON artifact (for checkpoint replay)
POST   /session/{id}/checkpoint/evaluate  ← Re-run checkpoint evaluation
GET    /guardrails             ← Current guardrail config
PUT    /guardrails             ← Update guardrail defaults
POST   /tasks                  ← Manual task row API; normal intake uses estimation
PUT    /tasks/{id}             ← Update task (estimate, status)
POST   /estimate               ← Estimate tokens + recommend model for a task description
GET    /dashboard              ← Aggregate analytics (all sessions)
GET    /alarms                 ← Alarm history with filters
POST   /alarms/{id}/resolve    ← Mark alarm as resolved
```

## Pillar 4: Alarms

Alarms produce **structured output** with named types, context, severity, and recommended action.

### Alarm taxonomy


| Alarm Type           | Trigger                                        | Severity | Context                                                 | Recommended Action                                                    |
| -------------------- | ---------------------------------------------- | -------- | ------------------------------------------------------- | --------------------------------------------------------------------- |
| `BUDGET_YELLOW`      | Session enters yellow zone (>60% cap)          | LOW      | Current session spend, remaining budget, zone threshold | Inject wrap-up context into agent; no user action needed              |
| `BUDGET_RED`         | Session enters red zone (>85% cap)             | MEDIUM   | Current session spend, remaining budget, zone threshold | Notify user via configured channel; agent continues                   |
| `DAILY_CAP_EXCEEDED` | Daily token cap reached                        | HIGH     | Daily total, per-session breakdown, timestamp           | Notify user; sessions are not blocked — governance is visibility-only |
| `LOOP_DETECTED`      | Same tool + same input hash repeated ≥ N times | MEDIUM   | Tool name, input hash, repetition count, timestamps     | Notify user; agent continues — human decides whether to intervene     |
| `SESSION_TIMEOUT`    | Wall-clock time exceeded                       | MEDIUM   | Session duration, timeout threshold, last tool call     | Notify user; save checkpoint; agent continues                         |
| `TOOL_CATEGORY_BIAS` | One tool category >50% of session budget       | LOW      | Category name, percentage, tool breakdown               | Inject warning context into agent                                     |
| `CHECKPOINT_FAIL`    | Any checkpoint evaluated as fail               | MEDIUM   | Checkpoint name, fail reason, session ID                | Escalate to human for review; halt task pipeline until resolved       |


### Alarm structure

Every alarm is a JSON object:

```json
{
  "id": "alarm_abc123",
  "type": "BUDGET_RED",
  "severity": "MEDIUM",
  "session_id": "sess_xyz789",
  "timestamp": "2026-06-12T14:30:00Z",
  "context": {
    "current_spend": 178000,
    "session_cap": 200000,
    "zone": "red",
    "percentage": 0.89
  },
  "recommended_action": "Notify user; agent continues. Review session in portal."
}
```

## Human-in-the-Loop Escalation

The harness does not make decisions for the human. It surfaces what it knows, recommends an action, and defers. The human always has the final say — this is by design, not a limitation.

### Escalation paths

| Path | Trigger | Harness action | Human decision |
|---|---|---|---|
| **Budget override** | Task estimate exceeds remaining daily budget | Warning banner on AGILE Board: "Estimated 200K exceeds remaining 100K. The daily cap alarm will fire." | Override and dispatch anyway, reduce the estimate, or cancel |
| **Daily cap exceeded** | `DAILY_CAP_EXCEEDED` alarm fires mid-session | Notification + "Raise budget" button in portal | Raise the cap, abort session, or let it continue |
| **Loop detected** | `LOOP_DETECTED` alarm fires | Notification: "Agent repeated read_file(path=X) 8 times." | Continue (agent is fine), abort session, or adjust guardrail threshold |
| **Session timeout** | `SESSION_TIMEOUT` alarm fires | Notification + saved checkpoint | Continue, abort, or extend timeout |
| **Checkpoint failure** | Session ends with failed checkpoint | Card lands in Review column; pipeline halts | Review session report → manually advance to Done or re-dispatch |
| **Zone escalation** | Session enters yellow/red zone | Context injection + tool restrictions applied automatically; alarm logged | No action required — harness handles this. Human can override zone if needed |

### The principle

The harness constrains the **agent** (via system prompt, max_tokens, tool restrictions). It does not constrain the **human**. When the harness detects a problem, it tells you — clearly, with context and a recommendation — and you decide. This is the "stop and ask rather than guess" requirement from the challenge spec.

### Portal action buttons

Every alarm in the portal includes action buttons. The harness polls for the human's response and acts on it:

| Button | What it does |
|---|---|
| **Continue** | Dismiss alarm; agent keeps running with current constraints |
| **Abort session** | Terminate the agent process; session ends; artifacts saved |
| **Raise budget** | Update the daily cap; session re-evaluates zone and may return to green |
| **Adjust guardrail** | Modify the guardrail threshold (e.g., loop_threshold 5 → 10); changes take effect on the next request |

## Worker Adapter Interface (Swappable)

The harness is Worker-agnostic only after a Worker Adapter proves budget-authoritative tracking. A Worker Adapter is the launch/control integration for one coding agent: Claude Code, Codex, OpenCode, Hermes, or a custom command. The model recommendation is separate from the Worker Adapter.

An adapter is launchable from the AGILE Board only when setup verification proves token tracking works through either Harness Proxy traffic or trustworthy native CLI usage evidence. Observed-only logs are diagnostic, not launch-ready.

### How the agent connects

For proxy-governed sessions, the agent is pointed at the local harness URL instead of directly at the LLM provider. Native-usage adapters keep their own CLI auth/config and report trustworthy usage after the run.

```bash
# Hermes points at the harness
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=***  # harness-generated per-session key
```

### Session dispatch (when the user clicks "Launch")

1. **Harness checks launch guardrails**: Worker Adapter configured, token tracking verified, working directory valid, session key wiring available, selected model allowed.
2. **Harness creates a session record** in SQLite: `session_id`, task description, model, Worker Adapter, budget, guardrail overrides.
3. **Harness generates a session-scoped API key** (e.g., `sk-har...c3d4`). This key maps to the session — all requests carrying it are governed under that session's budget.
4. **Harness launches the Worker Adapter as a subprocess**, passing the harness URL and session key as environment variables or adapter-specific flags:

```python
# Inside the harness FastAPI app
subprocess.Popen(
    ["hermes", "--prompt", task.description],
    env={
        "OPENAI_BASE_URL": "http://localhost:8000/v1",
        "OPENAI_API_KEY": f"sk-harness-{session.id}",
        # Provider API key is NOT exposed to the agent —
        # the harness uses AGILE_AI_HTB_CONTROL_* upstream settings internally
    },
)
```

5. **Portal begins polling** `GET /session/{id}/report` for live updates.

### Per-request governance flow

On every API call from the agent:

```
Hermes: POST /v1/chat/completions
  Header: Authorization: Bearer sk-harness-a1b2c3
  Body: {model: "claude-haiku", messages: [...], tools: [...], max_tokens: 4096}

     │
     ▼
Harness (FastAPI endpoint):
  1. Look up session "sess_a1b2c3" from API key
  2. Evaluate live daily budget: 350,000 / 1,000,000 used → zone = green
  3. Layer 1: rewrite system prompt — "Be thorough: write tests..."
  4. Layer 2: max_tokens stays 4096 (green zone)
  5. Layer 3: tools unchanged (green zone — all tools available)
  6. Call the configured direct provider client:
       response = await llm_client.acompletion({
           "model": "gpt-4o-mini",
           "messages": messages,           # rewritten
           "max_tokens": 4096,             # clamped per zone
           "tools": tools,                 # filtered per zone
           "stream": True,
           "stream_options": {"include_usage": True},
       })
  7. The harness forwards to the configured upstream API and normalizes usage
  8. Extract token counts: response.usage.prompt_tokens=2150, completion_tokens=850
  9. Update session artifact: token_log.append({turn: 3, prompt: 2150, completion: 850})
  10. Update daily counter: 350,000 → 353,000
  11. Return response to agent (usage field stripped — the agent doesn't need it)
```

**Later, at >60% daily budget (yellow zone):**

The same flow, but:

- Step 3: system prompt → "Budget is limited. Prioritize core task. Be concise."
- Step 4: max_tokens → 2048
- Step 5: tools → `web_search`, `browser_*` removed

The agent cannot call those tools because they don't appear in the API response. The agent cannot produce long output because max_tokens is clamped. The only behavior change the agent "sees" is a different system prompt, but the harness constrains it at the transport level.

**At >85% daily budget (red zone):**

- System prompt → "Budget critical. Output only the final deliverable."
- max_tokens → 1024
- Tools → only `read_file`, `patch`, `terminal`

### Data plane vs. control plane

| Plane | Endpoint | Caller | Frequency |
|---|---|---|---|
| **Data plane** | `POST /v1/chat/completions` | The agent (Hermes) | Every API call — high volume, streaming |
| **Control plane** | `POST /session/start`, `GET /dashboard`, etc. | The portal (user) | On user action — low volume, request/response |

Both run in the same FastAPI process. The data plane is the governance hot path; the control plane serves the user experience.

### Swapping agents

The same mechanism works identically for any OpenAI-compatible agent:

```bash
# Claude Code
claude --api-base http://localhost:8000/v1 --api-key sk-harness-***

# Codex CLI
codex --base-url http://localhost:8000/v1 --api-key sk-harness-***

# Any OpenAI SDK client
client = OpenAI(base_url="http://localhost:8000/v1", api_key="sk-harness-***")
```

Each agent gets its own session key. The harness governs identically regardless of which agent produced the request. The configured direct provider client handles upstream forwarding while the proxy response remains OpenAI-compatible to Workers. The portal shows all sessions side-by-side for comparison, enabling the second-worker swap demo beat.

## Tech Stack


| Layer         | Technology                                | Rationale                                                    |
| ------------- | ----------------------------------------- | ------------------------------------------------------------ |
| Runtime       | Python 3.11+                              | Fast proxy, rich ecosystem                                   |
| Framework     | FastAPI                                   | Async-native, OpenAPI docs, Pydantic validation              |
| Database      | SQLite                                    | Zero setup, single file, survives Docker restarts via volume |
| Portal UI     | HTMX + Jinja2 + Chart.js                  | Server-rendered, no bundler, interactive via HTMX            |
| Charts        | Chart.js                                  | Token burn timeline, tool distribution pie                   |
| Notifications | Discord/Slack webhook + macOS `osascript` | Push alarms to user                                          |
| Container     | Docker (single Dockerfile)                | Local Control Plane/Portal smoke and packaging check         |


