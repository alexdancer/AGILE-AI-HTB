# AGILE-AI-HTB PRD

## Problem Statement

AI coding agents can burn through token budgets invisibly while they explore, loop, overuse expensive tools, or continue past the point where a human should decide whether to continue. A credible token-governance harness must prove that agent work and orchestration overhead are both visible, labeled, and governed. A passive task board or hidden estimator call is not enough: the project must show that AGILE-AI-HTB can estimate work, track planning tokens, verify Worker Adapter wiring, block ungoverned launches, and surface human decisions without constraining the human.

## Solution

Build AGILE-AI-HTB as a portal-first token-tracker harness for coding agents. The single FastAPI application provides:

- an OpenAI-compatible LLM proxy backed by LiteLLM,
- a SQLite Session Artifact Store,
- a portal with dashboard, AGILE Board, session reports, alarms, and Worker Setup,
- an Estimator LLM flow that tracks estimation spend as Orchestration Tokens,
- Worker Adapter presets for Claude Code, Codex, and OpenCode,
- Launch Guardrails that prevent the portal from launching unverified Workers.

The AGILE Board is the primary product workflow. Users enter coding tasks through **Estimate task** intake, review the Estimator LLM output, accept or override estimate/model choices, choose a launchable Worker Adapter, and launch governed work only when token tracking has been proven. The harness constrains the Worker through runtime guardrails but never constrains the human; warnings, budget overages, and alarms escalate with recommended actions.

## User Stories

1. As a user, I want the AGILE Board to estimate a task before launch, so that token budget is considered before agent work begins.
2. As a user, I want board columns `Estimated`, `Ready`, `Running`, `Review`, `Done`, and `Blocked`, so that the board reflects orchestration state rather than generic backlog state.
3. As a user, I want no normal unestimated Backlog, so that task intake remains tied to token planning.
4. As a user, I want Estimator LLM output to include token estimate, complexity, recommended model, confidence, rationale, assumptions, risk flags, and spike recommendation, so that I can judge the plan before launch.
5. As a user, I want Estimator LLM tokens labeled as Orchestration Tokens, so that planning overhead is visible and counted against the daily budget.
6. As a user, I want failed or unavailable estimation to create a Blocked task with manual estimate/model entry, so that the harness does not fake confidence with a hidden heuristic.
7. As a user, I want manual estimates clearly marked as manual, so that later analytics distinguish human-entered values from LLM estimates.
8. As a user, I want a task with a valid estimate but no verified Worker Adapter to remain Estimated with Launch disabled, so that setup gaps do not look like estimation failures.
9. As a user, I want to accept or override the estimate and model before launch, so that the harness advises but the human decides.
10. As a user, I want Worker Setup to show Claude Code, Codex, and OpenCode as first-class adapter presets, so that the project demonstrates real coding-agent targets.
11. As a user, I want unverified Worker Adapters to be visible but non-launchable, so that the portal honestly shows what is configured versus governed.
12. As a user, I want at least one adapter path to pass live verification, so that the demo proves real subprocess launch and token-row persistence.
13. As a user, I want Launch Guardrails to block launch unless the selected adapter is configured, workdir is valid, model is compatible, session key wiring exists, and token tracking has been verified.
14. As a user, I want adapter verification to launch the real adapter with a harmless sentinel prompt, so that a proxy-only smoke test cannot masquerade as governed Worker support.
15. As a user, I want adapter verification tokens labeled as `adapter_verification`, so that setup overhead is visible but not counted as task actuals.
16. As a user, I want Spike sessions for low-confidence tasks, so that an agent can inspect enough context to improve estimates before implementation.
17. As a user, I want Spike tokens labeled as `spike`, so that discovery spend is separate from implementation actuals.
18. As a user, I want daily budget totals to include Worker Session tokens and Orchestration Tokens, so that all spend counts toward the cap.
19. As a user, I want task execution analytics to separate Worker tokens from Orchestration Tokens, so that implementation actuals are not distorted by estimator/setup overhead.
20. As a user, I want session-scoped API keys, so that every Worker request maps to the correct governed session.
21. As a user, I want provider calls forwarded through LiteLLM, so that AGILE-AI-HTB can support multiple models/providers while owning governance logic.
22. As a user, I want green/yellow/red budget zones to rewrite prompts, clamp `max_tokens`, and filter tools, so that Workers are constrained at the transport level.
23. As a user, I want alarms to include type, severity, context, and recommended action, so that I know what decision is being requested.
24. As a user, I want alarm actions such as continue, abort, raise budget, and adjust guardrail, so that the human remains in control.
25. As a user, I want session reports with token totals, usage kind split, tool traces, alarms, zone snapshots, and checkpoint results, so that the session is auditable.
26. As a presenter, I want synthetic demo tasks and obviously fake data, so that the demo is safe and self-contained.
27. As a presenter, I want Claude Code, Codex, and OpenCode shown as supported adapter presets even if only one is verified locally, so that Launch Guardrails visibly prove the safety boundary.
28. As a presenter, I want current docs, tests, and demo seed data to match the canonical board states, so that the demo does not contradict the product story.

## Implementation Decisions

- Keep AGILE-AI-HTB as a single FastAPI process with proxy data plane, control API, and server-rendered portal.
- Use SQLite for sessions, tasks, token turns, tool traces, alarms, guardrail snapshots, checkpoint results, action history, and Worker Adapter configuration.
- Use LiteLLM as the provider transport for both Worker requests and Estimator LLM calls. The harness owns governance, usage labeling, and persistence.
- Add token usage labeling with `usage_kind`: `worker`, `estimation`, `spike`, or `adapter_verification`. Existing rows default to `worker`.
- Replace normal Backlog product behavior with canonical AGILE Board states: `Estimated`, `Ready`, `Running`, `Review`, `Done`, and `Blocked`.
- Treat `POST /tasks` / portal intake as **Estimate task** flow. Successful LLM estimation creates an Estimated task. Failed estimation creates a Blocked task that requires manual estimate/model entry.
- Do not silently use a heuristic as product fallback when Estimator LLM fails. Test fakes may exist for deterministic tests, but production behavior must be explicit.
- Store estimation metadata on tasks: source, confidence, rationale, assumptions, risk flags, budget note, and spike recommendation.
- Keep Estimator LLM configuration environment-driven for this milestone; do not add estimator settings UI before Worker Setup.
- Add Worker Setup as the source of truth for Worker Adapter configuration and verification.
- Implement Claude Code, Codex, and OpenCode as first-class adapter presets over a shared adapter contract. Do not assume identical environment variables or flags across adapters.
- Require adapter launch verification, not direct proxy verification, before marking an adapter launchable.
- Allow the demo environment to verify one adapter while showing the other first-class presets as unverified/non-launchable.
- Keep CLI scope to operator tasks such as serve and seed-demo. Portal/API remain the product UX.
- Update current product docs, tests, and demo seed data away from Backlog language. Historical implementation-plan notes may remain only if clearly marked as superseded.

## Testing Decisions

- Test external behavior through FastAPI routes and SQLite state rather than private implementation details.
- Keep default tests deterministic with fake LLM/adapter clients; do not call paid providers in CI/default test runs.
- Add/modify database tests for `usage_kind`, migration/backfill behavior, and token split totals.
- Add task API tests for successful LLM estimation, estimator failure to Blocked/manual path, manual estimate update, and no heuristic fallback.
- Add portal tests for canonical columns, Estimate task wording, launch-disabled state when no adapter is verified, and visible estimation metadata.
- Add Worker Setup tests for Claude Code, Codex, and OpenCode preset visibility and launchability status.
- Add adapter verification tests using fake subprocess/LLM traffic that proves sentinel response and token-row persistence.
- Add Launch Guardrail tests that block unconfigured, unverified, incompatible-model, invalid-workdir, or missing-session-key cases.
- Add demo invariant tests ensuring synthetic demo data remains obviously fake.
- Run targeted tests after each slice and `python -m pytest -q` before sign-off.

## Out of Scope

- Multi-user account management or hosted SaaS billing.
- Full production authentication beyond the existing operator portal token model.
- Implementing every adapter-specific edge case for Claude Code, Codex, and OpenCode before the first verified launch path works.
- Queueing, batching, or autonomous multi-agent scheduling.
- A frontend SPA or JavaScript build system.
- Enforcing budget decisions on the human. The harness constrains Workers and escalates to humans; it does not block human overrides.
- Real customer data or real-looking demo artifacts.

## Further Notes

- The shortest credible path is two slices: first make the portal truthful and estimator/orchestration spend tracked; then add Worker Setup, Launch Guardrails, and one live verified adapter path.
- The strongest demo claim is: “AGILE-AI-HTB tracks both Worker execution and orchestration overhead, and it refuses to launch unverified agents as governed work.”
- `CONTEXT.md` is the domain glossary and should be updated immediately when product terminology changes.
- `docs/HARNESS.md` remains the deeper architectural reference.
