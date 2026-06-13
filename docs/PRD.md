# AGILE-AI-HTB PRD

## Problem Statement

AI coding agents can burn through token budgets invisibly while they explore, loop, overuse expensive tools, or continue past the point where a human should decide whether to continue. Existing agent workflows usually expose cost after the fact, if at all. The user needs a harness that wraps a swappable coding worker, makes token spend visible while work is happening, progressively constrains agent behavior as budget pressure rises, and escalates decisions to a human instead of guessing.

## Solution

Build AGILE-AI-HTB: a token-tracker harness packaged as a single FastAPI application that acts as an LLM proxy, session control API, and lightweight portal. The worker points its API base URL at the harness. The harness forwards LLM calls through LiteLLM, records token usage and tool traces into SQLite-backed session artifacts, applies declared guardrails from `guardrails.yaml`, evaluates checkpoints, and shows the human an AGILE board, dashboard, session reports, alarms, and override actions.

The harness constrains the agent, not the human. Zone-based governance rewrites the system prompt, clamps `max_tokens`, and filters available tools as budget consumption rises. Alarms and checkpoint failures always surface structured context and recommended actions, while the human can continue, abort, raise budget, adjust guardrails, or re-dispatch.

## User Stories

1. As a user, I want to declare daily and per-session token budgets, so that token governance is explicit and reviewable.
2. As a user, I want token consumption to reset at local midnight, so that the daily budget matches how I think about work days.
3. As a user, I want a global daily budget bar, so that I can see current usage and time until reset.
4. As a user, I want a task board with Backlog, Estimated, Running, Review, and Done columns, so that agent work is visible as a workflow.
5. As a user, I want to create a task with a natural-language description, so that I can dispatch agent work from the portal.
6. As a user, I want the harness to estimate task token cost, so that I can understand budget impact before dispatch.
7. As a user, I want the harness to classify task complexity, so that a sensible model tier is recommended.
8. As a user, I want to override the estimated token budget, so that human judgment remains final.
9. As a user, I want to override the recommended model, so that the harness advises but does not decide for me.
10. As a user, I want a warning when a task estimate exceeds remaining daily budget, so that I can choose whether to continue.
11. As a user, I want to dispatch one task into one governed session, so that analytics map cleanly to a unit of work.
12. As a user, I want session-scoped API keys, so that every worker request maps to the correct session.
13. As a user, I want the worker to call the harness instead of the provider directly, so that governance happens transparently.
14. As a user, I want provider calls forwarded through LiteLLM, so that the harness can support multiple models and providers without provider-specific code in every feature.
15. As a user, I want prompt and completion token counts stored for every turn, so that I can audit spend.
16. As a user, I want LiteLLM cost calculation stored per turn, so that budget reports can show approximate dollar cost.
17. As a user, I want streaming responses supported, so that the proxy can govern real agent behavior.
18. As a user, I want streaming token usage read only from the final usage chunk, so that token counts avoid known intermediate-chunk inflation.
19. As a user, I want green/yellow/red budget zones, so that budget pressure changes behavior progressively.
20. As a user, I want green-zone sessions to keep full tools and response length, so that normal work is not over-constrained.
21. As a user, I want yellow-zone sessions to get concise prompt guidance, smaller `max_tokens`, and no expensive exploration tools, so that agents focus on completion.
22. As a user, I want red-zone sessions to get delivery-only prompt guidance, tight `max_tokens`, and only core delivery tools, so that the agent cannot keep exploring.
23. As a user, I want zone transitions to be recorded, so that reports explain why behavior changed.
24. As a user, I want `BUDGET_YELLOW` and `BUDGET_RED` alarms, so that budget pressure is visible in the portal.
25. As a user, I want `DAILY_CAP_EXCEEDED` alarms, so that exceeding the daily cap escalates to me rather than silently continuing.
26. As a user, I want loop detection based on repeated tool and input hashes, so that stuck behavior is surfaced quickly.
27. As a user, I want session timeout alarms, so that long-running sessions produce reviewable checkpoints.
28. As a user, I want tool-category budget bias alarms, so that over-reliance on one kind of work is visible.
29. As a user, I want checkpoint failures to move task cards to Review, so that suspicious sessions require human review.
30. As a user, I want each alarm to include type, severity, session id, context, and recommended action, so that I know what decision is being requested.
31. As a user, I want portal actions for continue, abort session, raise budget, and adjust guardrail, so that I can respond to alarms directly.
32. As a user, I want raw session artifacts, so that checkpoint evaluation can be replayed without re-running the agent.
33. As a user, I want a session report with token totals, tool breakdown, alarm history, zone timeline, checkpoint results, and final output summary, so that I can audit a session.
34. As a user, I want aggregate dashboard charts for token burn and tool distribution, so that I can understand spend patterns across sessions.
35. As a user, I want completed tasks to show estimated vs. actual tokens, so that future estimates improve.
36. As a user, I want failed or alarmed tasks to land in Review, so that completion requires an explicit human decision.
37. As a user, I want to re-run a completed task with a different model, so that I can demonstrate worker portability.
38. As a user, I want the same governance to apply to Hermes, Claude Code, Codex, or any OpenAI-compatible worker, so that the harness is agent-agnostic.
39. As a user, I want a local demo scenario with synthetic tasks, so that the harness can be shown without real customer data or risky production integrations.
40. As a presenter, I want seeded demo tasks with easy, modest, and complex examples, so that the demo shows routing, governance, alarms, review, and portability.

## Implementation Decisions

- Build one Python 3.11+ FastAPI service that contains the proxy data plane, control API, and server-rendered portal.
- Use SQLite as the only required datastore for sessions, tasks, token logs, tool traces, alarms, guardrail snapshots, checkpoint results, and action history.
- Use YAML guardrail defaults from `guardrails.yaml`; allow per-session overrides where needed.
- Use LiteLLM as the transport and provider abstraction layer. The harness owns governance before provider forwarding.
- Support OpenAI-compatible chat completions first through `/v1/chat/completions`.
- Implement streaming pass-through early enough to prove real proxy behavior, but keep non-streaming support for tests and smoke checks.
- Treat the daily budget as calendar-day local time, recalculated on every governed request.
- Implement three-layer graduated enforcement in a pure governance module: system prompt rewrite, `max_tokens` clamp, and tool filtering.
- Keep alarm generation in a dedicated domain module with stable alarm types and JSON-compatible payloads.
- Keep checkpoint evaluation stateless: it accepts a persisted session artifact and returns checkpoint results.
- Keep agent subprocess dispatch behind an adapter so the initial implementation can run a stub/local command while later integration launches Hermes or another worker.
- Build the portal with Jinja2 templates, HTMX interactions, and Chart.js charts; avoid a JavaScript build system for the challenge implementation.
- Build a synthetic `snip` demo project under a demo directory rather than recursively using the harness project as its own demo subject.
- Do not hard-stop sessions when budgets are exceeded. The harness constrains the worker and escalates to the human.
- Do not expose provider API keys to the worker. The worker receives only a harness session key.

## Testing Decisions

- Test external behavior rather than private implementation details.
- Unit-test guardrail loading, zone calculation, prompt rewriting, token clamping, and tool filtering.
- Unit-test alarm triggers for daily cap, session cap, budget zones, loop detection, timeout, tool-category bias, and checkpoint failure.
- Unit-test checkpoint evaluation from artifact-shaped data without running an agent.
- Integration-test the FastAPI API with an in-memory or temporary SQLite database.
- Integration-test `/v1/chat/completions` using a fake LiteLLM adapter so tests do not call paid provider APIs.
- Add a small smoke test for portal routes returning usable HTML.
- Add demo invariant tests proving all demo data is synthetic and isolated from real credentials or user data.
- Use real HTTP requests through FastAPI's test client for API behavior.
- Keep live provider calls out of the default test suite; document an optional manual smoke command for LiteLLM-provider verification.

## Out of Scope

- Production-grade authentication and multi-user account management.
- A hosted SaaS deployment or billing system.
- Full Anthropic-native API compatibility beyond OpenAI-compatible chat completions.
- Perfect token accounting for every possible provider edge case beyond LiteLLM's normalized usage fields.
- Complex queueing, batching, or multi-agent orchestration.
- A frontend SPA or heavy client-side app framework.
- Long-term analytics warehouse or external database dependency.
- Enforcing decisions on the human, such as blocking override actions or preventing dispatch.
- Real GitHub Gist sharing in the first harness milestone; it remains part of the synthetic demo project's complex task list.

## Further Notes

- The challenge narrative should emphasize the four pillars: declared guardrails, checkpoints, material handling, and alarms.
- The strongest demo beat is transport-level governance: the agent cannot ignore `max_tokens` clamps or missing tools because the harness modifies the request before forwarding.
- Human-in-the-loop language matters: alarms recommend actions; humans decide.
- The first implementation should bias toward a complete vertical slice over broad partial features: configure guardrails, start a session, proxy one request, record usage, apply zones, show a report, and render it in the portal.
- Existing design references live in `docs/HARNESS.md`, `docs/HARNESS-SUMMARY.md`, `docs/DEMO.md`, `CONTEXT.md`, and `guardrails.yaml`.
