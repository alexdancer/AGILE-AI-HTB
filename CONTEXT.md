# Context

## Harness
**Definition**: The governing framework that wraps a coding agent, providing guardrails, checkpoints, material handling, and alarms.
**Also known as**: AGILE-AI-HTB, Token-Tracker Harness.
**Relationships**: Governs a Worker. Declares Guardrails. Evaluates Checkpoints. Fires Alarms. Exposes Material Handling interfaces.

## Control Plane
**Definition**: The deployable Harness surface that owns the Portal, AGILE Board, budget governance, orchestration workflows, proxy, token accounting, and reports.
**Properties**: Can run as a hosted service. Coordinates work but does not itself guarantee access to a User's local repository or local coding-agent tools.
**Relationships**: Connects to Execution Backends. Receives Worker traffic through the Proxy Engine. Displays Project Capability.

## Execution Plane
**Definition**: The environment where repository access, Worker Adapter launch, and coding-agent execution actually happen.
**Properties**: May be a Local Runner on the User's machine, a Hosted Workspace/Sandbox, or an analysis-only backend with no launch capability.
**Relationships**: Executes Worker Sessions requested by the Control Plane. Provides Project Capability evidence.

## Execution Backend
**Definition**: A concrete execution mode available to the Harness for a Connected Project.
**Properties**: Supported backend types are Local Runner, Hosted Workspace/Sandbox, and analysis-only. A backend determines whether the project can only be analyzed or can also launch governed Worker Sessions.
**Relationships**: Supplies capabilities to the Control Plane. Must satisfy Launch Guardrails before a Task can run.

## Local Runner
**Definition**: A small process running near the User's local repository that connects to the Control Plane and executes Worker Adapter launches on that machine.
**Properties**: Has access to local repo paths and locally installed coding agents. In all-in-one local mode, it can run as a built-in Execution Backend inside the local Harness process. In hosted mode, it pairs with the hosted Control Plane, reports heartbeat/capabilities, and routes Worker model traffic through the Harness proxy for token tracking.
**Relationships**: An Execution Backend. Makes a Connected Project launch-ready when online, paired, and verified.

## Hosted Workspace
**Definition**: A server-side workspace, usually created from a Git URL, that the Control Plane can use for project analysis and eventually hosted Worker execution.
**Properties**: Initially useful for analysis-ready breakdown and estimation. Requires sandboxing, credentials policy, and Worker Adapter installation before it can become launch-ready.
**Relationships**: An Execution Backend. May support Hosted Sandbox execution in later phases.

## Project Capability
**Definition**: The Harness-visible readiness state of a Connected Project.
**Properties**: States include not connected, analysis-ready, launch-ready via Local Runner, launch-ready via Hosted Workspace/Sandbox, and blocked when no execution backend can satisfy launch requirements. The minimum scale proof is multiple projects or execution backends visible in one Control Plane: at least one launch-ready OpenCode path, one analysis-ready path, and one blocked/non-launchable path.
**Relationships**: Shown in the Portal. Feeds Launch Guardrails and determines whether board tasks can launch or only be estimated. The first implementation slice is a local execution slice that proves OpenCode can be verified and launched through the Harness Proxy with token ledger evidence before broader dashboard scale states are built. The first OpenCode launch proof is read-only repo inspection that produces a session report artifact; a tiny docs-only change can follow after that succeeds.

## Repository Cleanliness Guardrail
**Definition**: The launch rule that prevents write-capable Worker Sessions from mixing agent edits with pre-existing user changes.
**Properties**: Read-only sessions may run in a dirty repository. Write-capable sessions require a detected git repository, current branch visibility, and a clean working tree before launch. Write-capable sessions create a task branch before launching the Worker.
**Relationships**: Part of Launch Guardrails. Applies to Local Runner and Hosted Workspace execution backends before write-capable Tasks run.

## Task Branch
**Definition**: The git branch created by the Harness for a write-capable Worker Session.
**Properties**: Named with the task identity, for example htb/task-123-short-title. Created only after the Repository Cleanliness Guardrail passes. Read-only sessions do not create task branches. The Worker edits on this branch, but the Harness owns committing: after configured verification passes, the Harness creates the commit with task/session metadata.
**Relationships**: Belongs to a Task and Worker Session. Shown in the Session Artifact and Portal review flow.

## Harness-Owned Commit
**Definition**: A git commit created by the Harness after a write-capable Worker Session completes and configured verification passes.
**Properties**: The Worker may edit files but should not directly own final git history. Commit requires the Project Profile test command to pass when configured and a Harness-generated git diff review summary. If no test command is configured, verification is marked missing test command and manual approval is required before commit. Commit messages include task/session metadata and behavior-specific summary. If verification fails, changes remain uncommitted for review or retry.
**Relationships**: Created on a Task Branch. Referenced by the Session Artifact and Portal review flow.

## Blocked Worker Session
**Definition**: A Worker Session that cannot continue because of a hard safety, workflow, dependency, or manual blocker rather than a retryable adapter runtime failure.
**Properties**: The Harness preserves logs, token ledger entries when present, failure reason, branch name, and any uncommitted diff. Hard safety examples include read-only project mutation and write-capable verification failure requiring manual intervention. Retryable operational failures such as adapter timeout, nonzero exit, or missing authoritative usage after a launch attempt return the Task to Estimated with launch-error evidence instead of making it Blocked.
**Relationships**: Moves or keeps the Task in Blocked only for hard blockers. Operational launch failures are recorded on the Worker Run and keep the Task relaunchable from Estimated.

## Optional Pull Request
**Definition**: A pull request opened from a Harness-created Task Branch after a Harness-Owned Commit exists.
**Properties**: Not required for the first local execution slice. Available only when a GitHub remote is detected and GitHub CLI authentication is available. The Portal may show an optional Open PR action, but lack of PR capability does not block local branch, commit, or session artifact completion.
**Relationships**: Follows Harness-Owned Commit. References the Task Branch, verification result, and Session Artifact.

## Operator Command
**Definition**: A small administrative entrypoint for starting AGILE-AI-HTB and preparing demo data, not the product user experience.
**Also known as**: `htb`.
**Relationships**: Starts the Harness. Seeds Tasks for the Portal. Does not replace Portal workflows for task, session, alarm, or report management.

## Worker
**Definition**: The AI coding agent being governed by the harness — the entity that consumes tokens by making API calls and invoking tools.
**Also known as**: Agent, Coding Agent.
**Properties**: Swappable (OpenCode, Claude Code, Codex CLI, Hermes, or another coding-agent harness). May use Harness Proxy traffic, native CLI usage reporting, or non-authoritative process/log observation depending on the selected Worker Adapter Tracking Mode.
**Relationships**: Governed by the Harness. Consumes a Token Budget. Produces Session Artifacts.

## Worker Adapter
**Definition**: The Harness integration that configures, validates, launches, and observes an installed local coding-agent CLI such as OpenCode, Claude Code, Codex, Hermes, or a custom command.
**Properties**: Has a CLI command, working directory, model discovery path, launch command, supported models, tracking mode, and verification status. First-class Worker Adapter presets include OpenCode, Claude Code, Codex, and Hermes; custom command support may exist for extensibility but is not the primary demo path. OpenCode is the first verified local Worker Adapter target. Adapter verification must exercise the real CLI launch path with a harmless sentinel prompt; install-only checks are not launch proof. Proxy governance is one tracking mode, not the definition of a Worker Adapter. The Portal may show all first-class adapters even when only one is verified in the current environment; Launch Guardrails keep unverified or non-authoritative adapters non-launchable for governed Tasks.
**Relationships**: Selected by the User before launch. Has a Worker Adapter Tracking Mode. Must pass Launch Guardrails before the AGILE Board can dispatch a governed Task to a Worker.

## Worker Adapter Tracking Mode
**Definition**: The verified method by which the Harness proves token usage for a Worker Adapter launch.
**Properties**: `proxy_governed` means Worker model traffic flows through the Harness Proxy and is budget-authoritative. `native_usage` means the coding-agent CLI emits trustworthy machine-readable token usage evidence and is budget-authoritative when verified. Trustworthy native usage includes the selected model, prompt/input tokens, completion/output tokens, total tokens, exit status, and evidence binding the usage to the launched Worker Run. Approximate, scraped, human-readable, model-less, or unbound usage evidence is not authoritative and leaves the adapter `observed_only`. `observed_only` means the Harness can observe process/log evidence but cannot prove governed token usage, so it is not launchable for governed Tasks from the normal AGILE Board. Observed-only adapters may run only from a separate Worker Setup diagnostic/test flow that records command started, stdout/stderr, exit code or timeout, detected model if available, and an explicit not-budget-authoritative warning without changing task state or showing a Launch-ready badge.
**Portal labels**: `proxy_governed` displays as **API / Proxy: Governed through Harness Proxy**. `native_usage` displays as **CLI: Track native usage after run**. `observed_only` displays as **CLI: Observe command only**. Portal copy must not use the generic label "Governed" for all launchable adapters; it should separately show launch readiness, tracking label, runtime request guardrail availability, and accounting authority.
**Relationships**: Belongs to a Worker Adapter. Feeds Launch Guardrails, Orchestration Tokens, Worker Session accounting, and Portal launch readiness labels.

## Worker Setup
**Definition**: The user-facing configuration workflow for choosing and validating which Worker Adapters can be launched by the AGILE Board.
**Properties**: Shows adapter configuration, verification results, launchable status, and the default Worker Adapter. The Settings area is the source of truth; the AGILE Board displays the selected adapter status and links back to setup when launch is blocked.
**Relationships**: Produces launchable Worker Adapters. Supplies Launch Guardrail evidence for AGILE Board dispatch.

## Session
**Definition**: A single invocation of the Worker, bounded by start and end. The harness's primary unit of governance.
**Properties**: Has a token budget, a wall-clock duration, a set of tool invocations, and a zone state (green/yellow/red).
**Relationships**: Belongs to a Project. Consists of Tool Invocations. Evaluated by Checkpoints. Produces a Session Artifact.

## Worker Run
**Definition**: The persisted execution attempt created when the AGILE Board launches an Estimated Task through a Worker Adapter.
**Properties**: Created before the adapter subprocess starts and linked to the Task and Session. Records adapter identity, selected model, tracking mode, redacted command plan metadata, status, stdout/stderr evidence, return code, timeout or error details, and completion timestamps. Runs outside the HTTP request lifecycle so the Portal can return immediately while the Worker continues. Duplicate active Worker Runs for the same Task are rejected or mapped to the existing active run. Successful runs with required evidence move the Task to Review. Retryable operational failures such as timeout, nonzero exit, or missing usage evidence return the Task to Estimated with sanitized launch evidence and keep it relaunchable.
**Relationships**: Belongs to a Task and Session. Produced by Task Launch. Supplies Review evidence, Session Artifact evidence, Token Budget reconciliation, and launch failure diagnostics.

## Task
**Definition**: A user-approved unit of coding work from the AGILE Board, with a description and an optional token estimate. Advisory, not enforced by the harness.
**Properties**: Has a description, acceptance criteria, an estimated token cost, recommended model, selected/default Worker Adapter at launch, actual token cost (populated after the session completes), and metadata for intake source, launch evidence, review prompts, decisions, and blockers.
**Relationships**: May originate from manual entry, Markdown task intake, Markdown plan import, or long-task decomposition. Dispatched to a Session through a Worker Run. Resides on the AGILE Board.

## Markdown Task Intake
**Definition**: The board intake path that accepts multi-line Markdown text or an uploaded `.md` task file and turns it into one or more estimated Task cards.
**Properties**: Uploaded `.md` file content takes precedence over pasted text when both are supplied. Empty content and unsupported file types are rejected with a clear validation error. Markdown structure is evidence for task breakdown, not the source of truth for Tasks: checklist items, bullets, headings, constraints, non-goals, and verification notes must be semantically classified before any board Task is created. Markdown intake always shows a Task Breakdown Review before estimation, even when the Task Breakdown Agent decides the Markdown describes one coherent Task. Only accepted single-task decisions or vertical-slice candidates become estimated Task cards. Constraints and verification notes are preserved as candidate task metadata or acceptance criteria, not estimated as standalone work. Deterministic Markdown parsing may supply structure hints to the Task Breakdown Agent, but product intake must not expose or silently use deterministic splitting as a fallback or quick-import mode for creating Tasks.
**Relationships**: Feeds the Task Breakdown Agent and Task Estimation. Used by the long synthetic OpenCode comparison task and ordinary operator-entered Markdown plans.

## Proposed Task Breakdown
**Definition**: A human-reviewed set of smaller candidate Tasks produced from a Markdown plan or oversized task before anything is added to the AGILE Board.
**Properties**: Uses tracer-bullet vertical slices: each proposed Task should be independently grabbable, narrow, demoable or verifiable on its own, and should cut through the needed product layers rather than splitting work by technical layer. Produced by a Task Breakdown Agent that reads all manual task input and Markdown imports, decides whether the work is a single Task or should be separated into multiple Tasks, and explains the decision. Shows candidate task titles, implementation prompts, acceptance criteria, lightweight recommended sequence, whether the slice is human-in-the-loop or autonomous, rejected non-task items with reasons, and decomposition confidence. Rejected/non-task items are shown explicitly rather than hidden so the User can see that constraints, non-goals, and verification criteria were preserved or deliberately excluded. Constraints may apply to the whole imported plan or to specific candidate tasks; plan-level/global constraints are the default unless the agent or User scopes them more narrowly. Accepted tasks inherit relevant constraints into task metadata or acceptance criteria before Task Estimation. Recommended sequence may be preserved as metadata or creation order, but the first product slice does not enforce hard inter-task dependency blocking. The first review UI supports practical editing: accept or reject candidates, edit candidate titles or implementation prompts, edit constraints and acceptance criteria text, accept a single-task decision, and submit accepted candidates to Task Estimation. It does not require a full planning editor for splitting, merging, drag reordering, or arbitrary field editing. It does not produce official token estimates or model recommendations. Proposed Task Breakdowns are durable review records, not transient form state: the source, candidates, rejected items, constraints, failure details, Task Breakdown Model, and linked orchestration token session are preserved for audit, resume, retry, and debugging. Proposed Task Breakdowns are always reviewed by the User before any candidate becomes an estimated AGILE Board Task; high-confidence candidates are not auto-created in the first product slice.
**Relationships**: Produced during task intake when the Task Breakdown Agent decides the input is multi-task work. Reviewed and edited by the User on a separate breakdown review page rather than as an AGILE Board column or inline board state. Accepting a breakdown immediately sends accepted candidates to Task Estimation and creates Estimated AGILE Board Tasks, then returns the User to the AGILE Board; there is no separate accepted-but-unestimated pseudo-backlog state in the first product slice. Rejected items do not enter the AGILE Board.

## Task Breakdown Agent
**Definition**: The harness-owned orchestration agent that reads incoming manual task text or Markdown plans and decides whether the work should remain one Task or become a Proposed Task Breakdown.
**Properties**: Uses the Harness direct-provider transport path so its spend is tracked as Orchestration Tokens labeled task breakdown. It uses a separate configurable Task Breakdown Model that may be stronger or more planning-oriented than the Estimator LLM while still remaining part of the control-plane/orchestrator model layer rather than the Worker Adapter model layer. It performs semantic decomposition rather than relying on simple length thresholds. It uses lightweight project context such as language, framework, test command, top-level folders, and project docs rather than inspecting arbitrary source files. It follows tracer-bullet vertical-slice rules and returns either a single-task decision or proposed smaller Tasks for human review. Its quality is evaluated with both product-flow tests and golden decomposition fixtures that assert vertical-slice candidates, constraints, verification criteria, non-goals, and rejected-as-task reasons for realistic Markdown plans. The first product slice invokes it for Markdown uploads, Markdown paste, and clearly oversized plain-text input; short plain-text tasks may go directly to Task Estimation to avoid unnecessary latency and orchestration-token spend. If the Task Breakdown Agent fails or returns invalid structure, the Harness shows an explicit breakdown-failed review/manual recovery screen with retry, manual candidate creation, single manual candidate, or cancel actions; it must not silently fall back to deterministic Markdown splitting or create an oversized Estimated Task from the whole source.
**Relationships**: Runs before Task Estimation for Markdown intake and clearly oversized plain text. Produces a Proposed Task Breakdown review for both multi-task work and single-task Markdown decisions; Task Estimation runs only after the User accepts reviewed candidates. Short plain-text tasks may bypass breakdown review and go directly to Task Estimation.

## Task Estimation
**Definition**: The LLM-assisted orchestration step where the Harness evaluates a Task before launch and produces a token estimate, complexity classification, model recommendation, confidence, rationale, assumptions, and risk flags.
**Properties**: Uses a harness-owned Estimator LLM distinct from the Worker model and Worker Adapter. Uses the Harness direct-provider transport path so estimator spend is tracked as Orchestration Tokens rather than hidden helper spend. Uses an accepted Task, lightweight project context, current budget context, and model-routing policy rather than a full repository scan. Produces structured output shown to the User before the Task becomes Estimated. The User can override the estimate or model before launch. If confidence is low, the User may run a Spike before accepting the estimate. If the Estimator LLM is unavailable or returns invalid output, the User may enter a manual estimate and model, clearly marked as manual rather than LLM-estimated. The Harness must not silently replace a failed Estimator LLM call with a heuristic product estimate. Manual estimates are launchable when required fields are present and Launch Guardrails pass. Estimator LLM tokens count against the daily budget as orchestration tokens, separate from Worker Session tokens.
**Relationships**: Runs after manual task entry or after the User accepts Proposed Task Breakdown items. Produces a Model Recommendation. May recommend a Spike. Successful estimation places a Task in Estimated; failed or invalid estimation places it in Blocked for manual estimate/model entry. Feeds Launch Guardrails and Session dispatch.

## Spike
**Definition**: A bounded pre-task Worker Session used to inspect enough project context to improve a low-confidence estimate before the real implementation begins.
**Properties**: Requires a launchable Worker Adapter because it is a Worker Session. By default it uses the same Worker Adapter and model intended for implementation, but the User may override to a cheaper or faster launchable adapter/model. It has no spike-specific token cap; normal daily and session guardrails still apply. It may inspect files, inspect configuration, and run targeted non-mutating tests or discovery commands, but must not modify production code, run destructive commands, broad test suites without approval, migrations, or commits. Its output is findings, revised estimate, risks, and launch recommendation.
**Relationships**: Triggered by low-confidence Task Estimation or by User choice. Counts against the daily budget as orchestration tokens labeled as spike, not Task actual implementation tokens. Automatically updates the Task estimate, recommended model, confidence, rationale, and risks, then returns the Task to Estimated with an updated-by-spike badge. The User still accepts the estimate and chooses the Worker before Launch.

## Orchestration Tokens
**Definition**: Tokens spent by the Harness itself to plan, estimate, validate, or coordinate work before or around Worker execution.
**Properties**: Count against the daily budget, but are labeled separately from Worker Session tokens so operator overhead does not distort task execution analytics.
**Relationships**: Produced by the Task Breakdown Agent, Task Estimation, Spikes, Worker Adapter verification, Agent Review, and reporting. Persisted token usage is labeled by usage kind such as worker, task breakdown, estimation, spike, adapter verification, or reporting with spend-category metadata when needed. Task Breakdown Agent tokens are labeled as task breakdown, not attached to Task implementation actuals, and shown as orchestration spend. Spike tokens are labeled as spike, not Task implementation actuals. Worker Adapter verification tokens are labeled as adapter verification, not attached to Task actuals, and hidden from the normal task board or marked as system verification. Agent Review/reporting tokens use the control-plane model and remain separate from Worker execution spend. Shown separately from Worker tokens in Portal analytics while still counting toward the daily budget.

## Token Budget
**Definition**: A cap on token consumption, declared at two levels — daily (across all sessions) and per-session.
**Also known as**: Budget, Cap.
**Properties**: Expressed in tokens. Daily budget includes both Worker Session tokens and Orchestration Tokens. Per-session budget applies to Worker Session tokens. Budget state gates new launches before they start, but does not automatically halt a Worker Session mid-task. When an estimate exceeds remaining budget before launch, the User may explicitly approve a budget override; the Session is tagged as a budget override and audited. `native_usage` overrides require explicit acknowledgement that native usage cannot be request-throttled mid-run and may reconcile as an overrun after completion. When exceeded during a running Session, the Harness records the overrun and raises alarms; user/admin manual abort remains available.
**Relationships**: Governed by Guardrails G1 and G2. Monitored by Checkpoint C1.

## Guardrail
**Definition**: A declared constraint that the harness enforces on the Worker. Every guardrail is explicit configuration, not implicit behavior.
**Properties**: Has a name, a threshold, and an enforcement action (context injection, alarm, or both). Never hard-stops the agent. Runtime request governance applies only when the Worker Adapter runs in `proxy_governed` mode and Worker model calls pass through the Harness Proxy. `native_usage` is budget-authoritative for accounting but limited to launch/review governance, preflight budget checks, post-run reconciliation, and alarms after usage is known. `observed_only` is process/log evidence only and is not governed-launchable.
**Relationships**: Declared in the Guardrail Configuration. Enforced by the Proxy Engine for `proxy_governed` sessions and by launch/review reconciliation for `native_usage` sessions. May trigger an Alarm.

## Launch Guardrail
**Definition**: A pre-run rule that prevents a Task from becoming Running unless the Harness can govern and observe the chosen Worker.
**Properties**: Validates that a Worker Adapter is configured, the working directory is valid, the selected model is allowed, and the selected tracking mode has proven budget-authoritative token usage. `proxy_governed` adapters require Harness Proxy session-key wiring. `native_usage` adapters require trustworthy native CLI usage evidence. `observed_only` adapters are not launchable for governed Tasks.
**Relationships**: Gates AGILE Board launch. Protects the token-tracker promise before a Session starts. Distinct from runtime Guardrails, which constrain Worker behavior during a Session.

## Checkpoint
**Definition**: An explicit pass/fail evaluation that runs at a Session boundary, inspecting the Session Artifact for behavioral signals.
**Properties**: Has explicit criteria, a result (pass/fail), and a timestamp. Stateless — re-evaluatable from the artifact alone.
**Relationships**: Evaluates a Session Artifact. May trigger an Alarm on failure. May escalate to a human.

## Alarm
**Definition**: A structured notification that something the harness governs has deviated from expected bounds.
**Properties**: Has a named type (e.g., BUDGET_RED, LOOP_DETECTED), a severity (LOW/MEDIUM/HIGH), context describing the deviation, and a recommended action.
**Relationships**: Triggered by a Guardrail violation or a Checkpoint failure. Routed to a human via a notification channel.

## Material Handling
**Definition**: The clean interfaces for passing work and results between the User, the Harness, and the Worker.
**Properties**: Comprises the Portal UI (AGILE Board, Dashboard) and the REST API (session management, analytics).
**Relationships**: Accepts Tasks from the User. Dispatches Sessions to the Worker. Returns Session Reports to the User.

## AGILE Board
**Definition**: The user-facing Kanban-style orchestration surface where the User enters or imports coding work, reviews harness estimates, selects a Worker, launches governed work, and tracks completion.
**Properties**: Columns represent orchestration state: Estimated (token/model recommendation produced and launchable once guardrails pass), Running (Worker Session active), Review (Session ended and awaits human review), Done (accepted), and Blocked (estimation failed or task needs human change before launch or continuation). There is no full Scrum/Jira workflow and no normal unestimated Backlog because task intake exists to break down, estimate, and budget token spend. A task with a valid estimate but no verified Worker Adapter remains Estimated with Launch available but guardrail-blocked rather than becoming Blocked. Each task card shows estimated vs. actual tokens, model recommendation, default Worker Adapter with per-task override, and linked Session results. Global budget state is visible while planning and dispatching work.
**Relationships**: Part of Material Handling. Contains Tasks. Produces estimates and Model Recommendations. Dispatches Estimated Tasks to a Worker through a Session. Returns Session Reports to the User. Accepts work through manual single-task entry, Markdown plan import with task breakdown, or long-task decomposition into multiple smaller Tasks. Current product docs, demo data, and tests should use the canonical board states; old Backlog language belongs only in clearly historical implementation plans.

## Review Disposition
**Definition**: The operator-controlled workflow for deciding what happens after a successful Worker Run moves a Task into Review.
**Properties**: Review cards expose Agent Review, Mark Done, and Block actions when completed Worker Run or Session evidence is present. The operator may save a review prompt or focus while leaving the Task in Review. Mark Done records an accepted operator decision and moves the Task to Done. Block requires a human-readable reason, records blocked review metadata, and moves the Task to Blocked. Review evidence remains linked to the Task regardless of disposition.
**Relationships**: Follows Worker Run completion. Uses Worker Run, Session, token, launch, and optional operator-focus evidence. Updates Task metadata and AGILE Board state.

## Agent Review
**Definition**: A control-plane review pass over completed Worker execution evidence, requested by the operator from a Review task card.
**Properties**: Uses the AGILE-AI-HTB control-plane/orchestrator model, not the Worker Adapter model or Worker auth. Builds the review request from Task description, Worker Run evidence, Session Artifact evidence, token evidence, launch metadata, and the latest operator review prompt when present. Persists review status, model, timestamp, summary, recommendation, findings, and sanitized failure details. Agent Review never automatically moves the Task to Done, Estimated, or Blocked; the operator still chooses the disposition.
**Relationships**: Part of Review Disposition. Consumes Orchestration Tokens/reporting spend and produces review metadata displayed on the AGILE Board.

## Long OpenCode Comparison Demo
**Definition**: A synthetic DEMO 2099 task and runbook that compare direct OpenCode execution against AGILE-AI-HTB-governed OpenCode execution on the same long coding task.
**Properties**: Uses `demo_tasks/DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md` and `docs/DEMO_2099_OPENCODE_COMPARISON_RUNBOOK.md`. The task builds a local-only `incident-ledger` Python CLI with ingest, list, dedupe, score, report, and export commands. Direct OpenCode usage is preserved as external baseline evidence, while the harness path demonstrates estimate, launch guardrails, budget gate or override acknowledgement, Worker Run evidence, token ledger, alarms, and Review workflow. All demo data must stay obviously synthetic: DEMO markers, 2099 dates, `.invalid` emails, DEMO addresses, and 999-style account IDs, with fake-data invariant tests guarding the artifacts.
**Relationships**: Exercises Markdown Task Intake, Worker Adapter tracking modes, Worker Run lifecycle, Token Budget governance, and Review Disposition without introducing real customer data or real external service calls.

## Model Recommendation
**Definition**: The harness's suggested model tier for a given Task, based on task complexity classification with an optional budget-aware downgrade.
**Properties**: Has a complexity class (simple/modest/complex), a recommended model name, and a budget-aware clamp that downgrades when daily budget is low. Pre-selected in the Portal; user can override. Does not choose the Worker Adapter.
**Relationships**: Produced during Task estimation. Feeds into Session dispatch as the model the Worker uses. Checked against the selected Worker Adapter for compatibility before launch.

## Proxy Engine
**Definition**: The component that intercepts all API calls between the Worker and the LLM provider, counting tokens and injecting guardrail context.
**Properties**: Transparent to the Worker — the Worker points its API base URL at the harness. Extracts token counts from provider `usage` fields.
**Relationships**: Enforces Guardrails. Records Tool Invocations. Feeds the Session Artifact Store.

## Session Artifact
**Definition**: The complete record of a Session — token logs, tool traces, alarm history, guardrail state snapshots, and checkpoint results. Persisted for replay.
**Properties**: A JSON-structured bundle. Stateless checkpoint evaluator can re-read it to re-evaluate with updated thresholds.
**Relationships**: Produced by a Session. Evaluated by Checkpoints. Stored in the Session Artifact Store.

## Budget Zone
**Definition**: A graduated classification of how much of the shared daily token budget has been consumed — green (normal), yellow (conserve budget), or red (delivery-only).
**Properties**: Thresholds declared in the Guardrail Configuration (e.g., green <60%, yellow <85%, red ≤100%). Drives graduated governance of the Worker.
**Relationships**: Governed by Guardrail G3. Transitions between zones as daily tokens are consumed. Triggers BUDGET_YELLOW and BUDGET_RED alarms. Distinct from per-session caps, which trigger alarms/checkpoints but do not define the zone.

## Escalation
**Definition**: The path by which the harness brings a decision to the human rather than guessing — when an alarm fires or a checkpoint fails.
**Properties**: Delivered as a notification with a deep link to the Portal. Human responds with an action (continue, abort, raise budget).
**Relationships**: Triggered by Alarms and Checkpoint failures. Resolved by human action in the Portal.
