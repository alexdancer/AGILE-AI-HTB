# AGILE-AI-HTB Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Finish the working AGILE-AI-HTB demo by making the portal truthful, tracking Estimator LLM spend as Orchestration Tokens, and proving Worker launch through verified Claude Code/Codex/OpenCode adapter presets.

**Architecture:** Keep the existing FastAPI + SQLite + Jinja2 portal. First align the current board/task/token schema with the resolved domain model. Then add Estimator LLM as a first-class harness operation. Finally add Worker Setup, Launch Guardrails, and adapter verification so the portal can launch only Workers whose token traffic is proven to pass through the harness proxy.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, SQLite, LiteLLM, Jinja2/HTMX, pytest, Docker.

---

## Current state and guardrails for implementation

- Existing repo already has FastAPI app, SQLite persistence, proxy/token recording, portal pages, CLI/Docker work, and tests.
- Repo is dirty; re-run `git status --short --branch` before each major edit and do not commit unless the user asks.
- Product UX is portal/API-first. CLI remains operator-only (`serve`, `seed-demo`), not a parallel CRUD workflow.
- Do not preserve `Backlog` as normal product state. Historical docs may mention it only if clearly marked superseded.
- Do not silently use a heuristic estimate in product flow when Estimator LLM fails.
- Default tests must not call paid LLM providers or require locally authenticated Claude/Codex/OpenCode installs.

---

## Implementation status (as of 2026-06-13)

### Backend: built and test-covered

| Layer | Status | Notes |
|---|---|---|
| DB schema (`db.py`) | ✓ | `token_turns.usage_kind`, `worker_adapters` table, `tasks.metadata_json`, migrations |
| Board columns (`portal.py`) | ✓ | Canonical: Estimated → Ready → Running → Review → Done, plus Blocked |
| Task CRUD (`tasks.py`) | ✓ | Canonical statuses enforced; non-canonical status → Blocked |
| Estimator LLM (`estimation.py`) | ✓ | `EstimateResult` shape, fake-LLM test path, `usage_kind='estimation'` persistence |
| `POST /estimate` route | ✓ | Calls estimator, creates Estimated or Blocked task |
| Worker adapter presets (`db.py`) | ✓ | Claude Code, Codex, OpenCode seeded on init |
| Launch guardrails (`launch_guardrails.py`) | ✓ | Adapter configured, verified, workdir valid, model supported, proxy wiring |
| `POST /tasks/{id}/launch` route | ✓ | Guardrail check → session start via runner |
| Proxy (`proxy.py`) | ✓ | `/v1/chat/completions`, governance, token recording, alarms |
| Portal auth (`auth.py`) | ✓ | Cookie-based, login/logout, `require_portal_auth` |
| Docker / render.yaml | ✓ | Image builds, health check passes |

### Portal UI: display-only, no intake forms

| Page | Renders | Can interact? |
|---|---|---|
| `/login` | ✓ | ✓ (token form) |
| `/dashboard` | ✓ | ✗ (read-only metrics) |
| `/board` | ✓ | ✗ **No task intake form.** Cards displayed but no text input to create/estimate a task. Launch buttons hidden because no verified worker adapter exists. |
| `/settings/workers` | ✓ | ✗ **No configuration form.** Three preset cards visible but no way to set workdir, models, or trigger verification. |
| `/sessions` | ✓ | ✗ (read-only list) |
| `/sessions/{id}` | ✓ | ✗ (read-only report) |

### What the portal needs to close the loop

1. **Task intake form on `/board`** — text input + "Estimate task" button that POSTs to `/estimate`, HTMX-swaps the new card into the Estimated column.
2. **Worker adapter configuration on `/settings/workers`** — form per adapter card to set `workdir`, select supported models, and trigger verification (which calls the adapter's verification template against a test prompt).
3. **Launch button conditional logic** — currently hidden when no verified adapter exists. Needs to show when `has_verified_worker_adapter` is true AND the task has a matching model.

Until these three portal forms exist, the demo loop requires `curl` for every step. The backend can handle every state transition correctly — the portal just can't drive them yet.

---

## Slice 1: Truthful board and token usage labeling

### Task 1.1: Add `usage_kind` to token turns

**Objective:** Label token spend as Worker or Orchestration spend while keeping daily totals inclusive.

**Files:**
- Modify: `src/agile_ai_htb/db.py`
- Modify: `tests/test_db.py`
- Inspect callers: `src/agile_ai_htb/routes/proxy.py`, `src/agile_ai_htb/routes/portal.py`, tests that call `record_token_turn`

**Steps:**
1. Add `usage_kind text not null default 'worker'` to `token_turns` schema.
2. Make `init_db()` migrate existing databases by adding the column when missing.
3. Extend `record_token_turn(..., usage_kind='worker')` and persisted artifact rows.
4. Add helper(s) for token totals by kind if useful for portal/dashboard.
5. Update existing tests/callers to expect default `worker`.

**Verification:**
- Run: `python -m pytest tests/test_db.py -q`
- Run: `python -m pytest tests/test_proxy_api.py tests/test_proxy_streaming.py -q`
- Expected: existing proxy token rows persist as `worker`; old DB migration path passes.

### Task 1.2: Replace board columns with canonical states

**Objective:** Make the live portal match the domain model.

**Files:**
- Modify: `src/agile_ai_htb/routes/portal.py`
- Modify: `src/agile_ai_htb/templates/board.html`
- Modify: `tests/test_portal.py`

**Steps:**
1. Change board columns to `Estimated`, `Ready`, `Running`, `Review`, `Done`, `Blocked`.
2. Remove `Other` as normal display state; decide whether unexpected statuses map to `Blocked` or a visually hidden/debug fallback in tests.
3. Update board subtitle and task card copy away from backlog language.
4. Add Launch-disabled messaging on Estimated cards when no verified Worker Adapter exists: “Configure Worker Adapter to launch.”
5. Update portal tests for six canonical columns and no Backlog.

**Verification:**
- Run: `python -m pytest tests/test_portal.py::test_board_renders_columns_and_task_cards -q`
- Run: `python -m pytest tests/test_portal.py -q`
- Expected: board HTML shows canonical states and no normal Backlog column.

### Task 1.3: Update task defaults and demo seed states

**Objective:** Stop creating ordinary Backlog tasks in API/demo paths.

**Files:**
- Modify: `src/agile_ai_htb/routes/tasks.py`
- Modify: `src/agile_ai_htb/db.py`
- Modify: `src/agile_ai_htb/demo_seed.py`
- Modify: `tests/test_tasks_api.py`
- Modify: `tests/test_demo_seed.py`
- Modify: `docs/mockup/js/fixtures.js` if present and still used by mockup/demo

**Steps:**
1. Change task creation default status from `Backlog` to `Estimated` only when estimate/model are supplied; otherwise prefer the Estimate task flow from Task 2.2.
2. For direct `POST /tasks` without estimate/model, either return `Blocked` with metadata reason or require the estimate flow. Choose the least invasive route that keeps existing API usable without lying.
3. Update demo seeded tasks to canonical states, likely `Estimated` for planned tasks and `Running`/`Review`/`Done` only when demo evidence exists.
4. Update tests that assert Backlog.

**Verification:**
- Run: `python -m pytest tests/test_tasks_api.py tests/test_demo_seed.py -q`
- Expected: no test expects Backlog as normal state.

---

## Slice 2: Estimator LLM as tracked orchestration

### Task 2.1: Add estimator settings

**Objective:** Configure Estimator LLM without building a settings UI.

**Files:**
- Modify: `src/agile_ai_htb/settings.py`
- Modify: `tests/test_settings.py`

**Steps:**
1. Add `estimator_model` setting from `TOKEN_TRACKER_ESTIMATOR_MODEL`.
2. Default to a cheap model from configured simple model routing if no env var is set, or a documented static default if guardrails are unavailable at settings construction time.
3. Keep existing `provider_api_key_env` behavior.

**Verification:**
- Run: `python -m pytest tests/test_settings.py -q`
- Expected: env override and default behavior pass.

### Task 2.2: Replace `/estimate` heuristic behavior with Estimator LLM contract

**Objective:** Estimate through LiteLLM and return structured output; failed estimation is explicit.

**Files:**
- Modify: `src/agile_ai_htb/estimation.py`
- Modify: `src/agile_ai_htb/routes/tasks.py`
- Modify: `tests/test_tasks_api.py`
- Possibly modify: `src/agile_ai_htb/llm.py`

**Steps:**
1. Define an `EstimateResult` shape containing token estimate, complexity, recommended model, confidence, rationale, assumptions, risk flags, spike recommendation, budget note, and source.
2. Build a strict JSON prompt with lightweight project context and model-routing policy.
3. Call the existing LiteLLM client path with the estimator model.
4. Parse and validate JSON. Invalid/missing fields raise a typed estimator failure.
5. In tests, inject/fake the LLM client instead of calling a provider.
6. Remove or quarantine the keyword heuristic so it is not product fallback.

**Verification:**
- Run: `python -m pytest tests/test_tasks_api.py -q`
- Expected: successful fake LLM estimation returns structured output; fake invalid response returns failure/Blocked path, not heuristic values.

### Task 2.3: Persist estimator token usage as `estimation`

**Objective:** Count Estimator LLM spend against the daily budget as Orchestration Tokens.

**Files:**
- Modify: `src/agile_ai_htb/estimation.py`
- Modify: `src/agile_ai_htb/db.py` if helper needed
- Modify: `tests/test_tasks_api.py` or add focused estimator tests

**Steps:**
1. Create a system/internal session or token-record path for estimator calls. Keep it clearly labeled so it does not appear as task implementation actuals.
2. Record estimator prompt/completion/total tokens with `usage_kind='estimation'`.
3. Store estimator metadata on the task.
4. Ensure dashboard daily totals include estimation tokens.

**Verification:**
- Run: `python -m pytest tests/test_tasks_api.py tests/test_db.py -q`
- Expected: estimation token row exists with `usage_kind='estimation'`; task actual tokens remain unset.

### Task 2.4: Implement Estimate task intake and manual fallback

**Objective:** Make task intake create Estimated or Blocked tasks according to estimator outcome.

**Files:**
- Modify: `src/agile_ai_htb/routes/tasks.py`
- Modify: `src/agile_ai_htb/templates/board.html`
- Modify: `tests/test_tasks_api.py`
- Modify: `tests/test_portal.py`

**Steps:**
1. Add/adjust endpoint used by portal intake so submitting a description runs estimation immediately.
2. On success, create/update task as `Estimated` with estimate/model/metadata.
3. On estimator unavailable/invalid, create task as `Blocked` with metadata reason and manual estimate/model requirements.
4. Support manual estimate/model update and mark `estimation_source='manual'`.
5. Show blocked manual-entry state in board HTML.

**Verification:**
- Run: `python -m pytest tests/test_tasks_api.py tests/test_portal.py -q`
- Expected: success path creates Estimated; failure path creates Blocked/manual; no hidden heuristic fallback.

---

## Slice 3: Portal analytics and current docs/demo cleanup

### Task 3.1: Show Worker vs Orchestration token split

**Objective:** Make orchestration spend visible in the portal.

**Files:**
- Modify: `src/agile_ai_htb/routes/portal.py`
- Modify: `src/agile_ai_htb/templates/dashboard.html`
- Modify: `src/agile_ai_htb/templates/session_report.html`
- Modify: `tests/test_portal.py`

**Steps:**
1. Compute daily total including all usage kinds.
2. Compute Worker token total and Orchestration token total separately.
3. Show split in dashboard.
4. Ensure session reports do not label estimation/adapter verification as task actuals.

**Verification:**
- Run: `python -m pytest tests/test_portal.py -q`
- Expected: dashboard renders daily total and usage-kind split without leaking secrets.

### Task 3.2: Update current product/demo docs away from Backlog

**Objective:** Remove demo-facing contradictions before implementation demo.

**Files:**
- Modify: `docs/DEMO.md`
- Modify: `docs/mockup/portal-v2.html`
- Modify: `docs/mockup/js/fixtures.js` if present
- Leave: `docs/IMPLEMENTATION-PLAN.md` current by this plan

**Steps:**
1. Replace Backlog demo flow with Estimate task intake.
2. Update board state descriptions to canonical columns.
3. Add Worker Setup / Launch disabled / verified adapter demo beat.
4. Keep all demo IDs and dates obviously synthetic.

**Verification:**
- Run: `python -m pytest tests/test_demo_fake_data_invariants.py -q` if present.
- Run: `python -m pytest tests/test_demo_seed.py -q`.
- Search: `Backlog|Create task` in current docs/code; only historical/superseded references should remain.

---

## Slice 4: Worker Adapter model and setup UI

### Task 4.1: Add Worker Adapter persistence

**Objective:** Store first-class Claude Code, Codex, and OpenCode adapter configuration and verification state.

**Files:**
- Modify: `src/agile_ai_htb/db.py`
- Add or modify tests: `tests/test_db.py`, possibly `tests/test_worker_adapters.py`

**Steps:**
1. Add `worker_adapters` table with id/kind/name/workdir/config JSON/supported models/default flag/verification status/evidence timestamps.
2. Seed or expose default preset rows for `claude_code`, `codex`, and `opencode`.
3. Provide CRUD-ish repository helpers for listing/updating/verifying adapter status.
4. Store verification evidence without secrets.

**Verification:**
- Run: `python -m pytest tests/test_db.py tests/test_worker_adapters.py -q`
- Expected: presets list, config updates persist, verification state round-trips.

### Task 4.2: Add `/settings/workers` portal page

**Objective:** Make Worker Setup the source of truth for adapter status.

**Files:**
- Modify: `src/agile_ai_htb/routes/portal.py` or add settings route module
- Create: `src/agile_ai_htb/templates/workers.html`
- Modify: `src/agile_ai_htb/templates/base.html`
- Test: `tests/test_portal.py` or `tests/test_worker_settings.py`

**Steps:**
1. Add navigation link to Worker Setup.
2. Render Claude Code, Codex, and OpenCode cards.
3. Show configured/unconfigured, verified/unverified, launchable/non-launchable, last evidence, and default adapter.
4. Do not show secrets or session keys.

**Verification:**
- Run: `python -m pytest tests/test_portal.py tests/test_worker_settings.py -q`
- Expected: all three presets visible; unverified adapters are clearly non-launchable.

---

## Slice 5: Launch Guardrails and adapter verification

### Task 5.1: Implement Launch Guardrail service

**Objective:** Centralize pre-launch checks.

**Files:**
- Create: `src/agile_ai_htb/launch_guardrails.py`
- Test: `tests/test_launch_guardrails.py`

**Steps:**
1. Define checks: adapter configured, token tracking verified, workdir valid, selected model allowed/compatible, session key/proxy wiring available.
2. Return structured pass/fail results with human-readable reasons.
3. Keep runtime Guardrails separate from Launch Guardrails.

**Verification:**
- Run: `python -m pytest tests/test_launch_guardrails.py -q`
- Expected: each failure mode blocks launch with precise reason.

### Task 5.2: Implement adapter command builders per preset

**Objective:** Avoid pretending all CLIs use identical flags/env vars.

**Files:**
- Create: `src/agile_ai_htb/worker_adapters.py`
- Test: `tests/test_worker_adapters.py`

**Steps:**
1. Define shared adapter interface: build verification command, build launch command, env injection, supported model check.
2. Implement preset classes/builders for Claude Code, Codex, and OpenCode.
3. Use documented/current CLI config patterns where verified; otherwise mark command template configurable.
4. Keep custom command optional only if it helps tests or extensibility.

**Verification:**
- Run: `python -m pytest tests/test_worker_adapters.py -q`
- Expected: each preset builds a command/env plan without leaking provider keys.

### Task 5.3: Implement adapter verification sentinel flow

**Objective:** Prove token tracking through a real adapter launch path.

**Files:**
- Modify: `src/agile_ai_htb/worker_adapters.py`
- Modify: `src/agile_ai_htb/db.py`
- Add route if needed: `src/agile_ai_htb/routes/workers.py`
- Test: `tests/test_worker_adapter_verification.py`

**Steps:**
1. Create disposable verification session.
2. Launch selected adapter with sentinel prompt.
3. Pass harness proxy URL and session-scoped API key according to adapter preset.
4. Require exact sentinel response `AGILE_AI_HTB_ADAPTER_OK`.
5. Verify a token row exists with `usage_kind='adapter_verification'` and selected model.
6. Verify no tool traces/file writes occurred.
7. Persist verification evidence/status.

**Verification:**
- Run: `python -m pytest tests/test_worker_adapter_verification.py -q`
- Expected: fake subprocess success marks adapter launchable only when sentinel and token row are present; missing token row fails.

---

## Slice 6: Task launch and one live adapter proof

### Task 6.1: Add task launch endpoint and board wiring

**Objective:** Move accepted tasks from Ready to Running only when Launch Guardrails pass.

**Files:**
- Modify: `src/agile_ai_htb/routes/tasks.py` or add launch route
- Modify: `src/agile_ai_htb/templates/board.html`
- Test: `tests/test_tasks_api.py`, `tests/test_portal.py`

**Steps:**
1. Add endpoint/action to accept estimate/model/adapter and evaluate Launch Guardrails.
2. If checks fail, keep task Estimated or Blocked according to failure type and show reason.
3. If checks pass, create session, generate session key, launch adapter subprocess, and move task Running.
4. On session completion, update task to Review or Done according to alarms/checkpoints.

**Verification:**
- Run: `python -m pytest tests/test_tasks_api.py tests/test_launch_guardrails.py tests/test_portal.py -q`
- Expected: unverified adapters cannot launch; verified adapter can start a governed session in tests.

### Task 6.2: Manual live verification for one adapter

**Objective:** Prove the demo environment can launch one real Worker Adapter through the harness.

**Files:**
- Update: `README.md` or `docs/DEMO.md` with exact local setup notes after proof

**Steps:**
1. Choose the locally available adapter among Claude Code, Codex, and OpenCode.
2. Configure its Worker Setup entry.
3. Run adapter verification from the portal or API.
4. Confirm sentinel output and token row persisted as `adapter_verification`.
5. Launch one Estimated task and confirm Worker token row persisted as `worker`.

**Verification:**
- Run targeted command/API flow used by the portal.
- Run: `python -m pytest -q` after any code changes.
- Expected: one adapter is verified/launchable; the other presets can remain visible as unverified/non-launchable.

---

## Slice 7: Final project quality gate

### Task 7.1: Run narrow and broad verification

**Objective:** Ensure the project is demo-ready.

**Commands:**
- `python -m pytest tests/test_db.py tests/test_tasks_api.py tests/test_portal.py -q`
- `python -m pytest tests/test_worker_adapters.py tests/test_launch_guardrails.py -q` if those files exist
- `python -m pytest -q`
- `python -m compileall src tests`
- `git status --short --branch`

**Expected:** tests pass, compile succeeds, changed files are reviewable, and no secrets are printed or committed.

### Task 7.2: Final stale-language scan

**Objective:** Catch contradictions before demo.

**Commands:**
- Search for `Backlog`, `Create task`, heuristic-estimator language, and proxy-only adapter verification claims.

**Expected:** Remaining stale terms are either removed, updated, or explicitly marked historical/superseded.

---

## Suggested execution order

1. Complete Slice 1 first; it removes the biggest product contradiction.
2. Complete Slice 2 next; it makes estimation credible and tracks Orchestration Tokens.
3. Complete Slice 3 before showing the portal to anyone.
4. Complete Slices 4-6 to prove launchability with Claude Code/Codex/OpenCode presets and at least one verified adapter.
5. Run Slice 7 before final handoff.
