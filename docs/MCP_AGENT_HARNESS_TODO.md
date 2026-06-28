# MCP Agent Harness Facade TODO

**Goal:** Let other AI agent harnesses drive AGILE-AI-HTB through MCP without bypassing the existing board, budget, Worker Run, and session-artifact guardrails.

**Verdict:** Plausible as a thin MCP facade over the existing Control Plane. Not plausible as universal token governance for arbitrary external agents unless their model calls go through the Harness Proxy or they provide trustworthy native usage evidence.

## Core boundary

```
Other agent harness
        │
        │ MCP tools/resources/prompts
        ▼
AGILE-AI-HTB MCP facade
        │
        │ existing DB / task / session / launch paths
        ▼
Control Plane ── Worker Adapter / Harness Proxy
```

The MCP layer should call existing paths, not duplicate orchestration logic.

## Intricacies to preserve

- **Model layers stay separate:** control-plane/orchestrator model handles estimates, breakdowns, reports, reviews; Worker Adapter models belong to OpenCode, Claude Code, Codex, Hermes, etc.
- **MCP is not token metering:** an MCP server sees tool calls, not the external harness's own LLM token usage.
- **Authoritative Worker usage needs one of:** `proxy_governed`, verified `native_usage`, or explicit non-authoritative `observed_only` diagnostic labeling.
- **Long-running launches return handles:** `launch_task` should return `worker_run_id`, `task_id`, status, and portal/report links; polling/fetch tools return progress and artifacts later.
- **Human-in-the-loop remains product law:** MCP must not silently mark tasks Done, auto-approve budget overrides, or bypass Review Disposition.
- **Repo access is execution-plane dependent:** hosted MCP cannot launch against a user's local path unless a verified Local Runner / execution backend is paired.
- **Results need caps:** default MCP responses should be summaries; raw stdout/stderr/session evidence should be separate paginated resources.
- **Secrets stay out:** expose adapter readiness/status, never secret values or raw env.

## Smallest credible MVP

- [ ] Add an optional MCP dependency/extra only when implementation starts.
- [ ] Add an explicit operator choice for optional Headroom integration (`https://github.com/headroomlabs-ai/headroom`) to compress tool outputs, logs, files, or RAG chunks before LLM use; do not make it required for installing or running AGILE-AI-HTB.
- [ ] Create a local stdio MCP server entrypoint, likely `htb-mcp`.
- [ ] Reuse existing SQLite/settings paths; no new tables for MVP.
- [ ] Expose read-only resources:
  - [ ] `htb://projects`
  - [ ] `htb://projects/{project_id}/board`
  - [ ] `htb://tasks/{task_id}`
  - [ ] `htb://worker-runs/{run_id}`
  - [ ] `htb://sessions/{session_id}/artifact`
  - [ ] `htb://budget/today`
  - [ ] `htb://worker-adapters`
- [ ] Expose conservative tools:
  - [ ] `list_projects()`
  - [ ] `list_board_tasks(project_id)`
  - [ ] `get_budget_status()`
  - [ ] `estimate_task(project_id, description)`
  - [ ] `create_task(project_id, description, estimate_tokens?, recommended_model?)`
  - [ ] `launch_task(task_id, adapter_id?, model?, budget_override=false, native_budget_acknowledged=false)`
  - [ ] `get_worker_run(run_id)`
  - [ ] `get_session_artifact(session_id)`
- [ ] Expose prompts after tools are useful:
  - [ ] `break_down_large_task`
  - [ ] `review_worker_run`
  - [ ] `summarize_session_artifact`
  - [ ] `prepare_acceptance_verification_task`

## Do not expose as MCP tools

- [ ] No generic shell execution.
- [ ] No arbitrary file write/read outside existing project/session evidence surfaces.
- [ ] No raw SQL.
- [ ] No secret configuration.
- [ ] No `mark_done` without explicit human/operator approval semantics.
- [ ] No launch path that skips `task_launch.launch_task` guardrails.

## Existing integration points

- FastAPI app factory: `src/agile_ai_htb/app.py`
- task routes and request models: `src/agile_ai_htb/routes/tasks.py`
- session report/artifact routes: `src/agile_ai_htb/routes/sessions.py`
- OpenAI-compatible Harness Proxy: `src/agile_ai_htb/routes/proxy.py`
- SQLite schema and helpers: `src/agile_ai_htb/db.py`
- Worker launch orchestration: `src/agile_ai_htb/task_launch.py`
- Worker Adapter command building/discovery: `src/agile_ai_htb/worker_adapters.py`
- canonical domain language: `CONTEXT.md`

## Later, only after local MVP proves useful

- [ ] Hosted Streamable HTTP MCP transport.
- [ ] Scoped auth tokens / OAuth-style auth for hosted use.
- [ ] Per-project permissions: read, task-write, launch, review, admin.
- [ ] Local Runner pairing flow for remote control-plane use.
- [ ] Pagination for large artifacts and event logs.
- [ ] Audit events for every mutating MCP tool call.
- [ ] Optional external-usage ingestion contract, clearly separate from authoritative proxy/native usage.

## Product claim to keep honest

AGILE-AI-HTB can expose governed task, estimate, launch, run-inspection, and artifact workflows to other harnesses through MCP.

It cannot govern arbitrary external-agent token spend unless the external harness routes traffic through AGILE-AI-HTB or gives trustworthy run-bound usage evidence.
