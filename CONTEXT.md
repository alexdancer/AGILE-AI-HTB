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
**Definition**: A Worker Session that cannot complete successfully because the Worker crashed, timed out, exceeded budget, failed verification, or produced no observed Harness Proxy traffic.
**Properties**: No automatic retry in the first implementation. The Harness preserves logs, token ledger entries, failure reason, branch name, and any uncommitted diff. Failure reasons include adapter crash, budget exceeded, timeout, verification failed, and no model call observed.
**Relationships**: Moves the Task to Blocked. May leave a Task Branch with uncommitted changes for user review or later retry.

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
**Properties**: Swappable (Hermes, Claude Code, Codex CLI). Communicates via an OpenAI-compatible API.
**Relationships**: Governed by the Harness. Consumes a Token Budget. Produces Session Artifacts.

## Worker Adapter
**Definition**: The Harness integration that configures, validates, launches, and observes one kind of Worker such as Claude Code, Codex, OpenCode, Hermes, or a custom command.
**Properties**: Has a launch command, working directory, model support, session key wiring, and token-tracking verification status. First-class Worker Adapter presets include OpenCode, Claude Code, Codex, and Hermes; custom command support may exist for extensibility but is not the primary demo path. OpenCode is the first verified local Worker Adapter target. Adapter verification requires a real sentinel call through the Harness Proxy that records token usage under an adapter verification session; install-only checks are not launch proof. Provider API keys live only in the Harness; Workers receive only a session-scoped Harness key and Harness Proxy base URL so they cannot bypass token tracking. The Portal may show all first-class adapters even when only one is verified in the current environment; Launch Guardrails keep unverified adapters non-launchable.
**Relationships**: Selected by the User before launch. Must pass Launch Guardrails before the AGILE Board can dispatch a Task to a Worker.

## Worker Setup
**Definition**: The user-facing configuration workflow for choosing and validating which Worker Adapters can be launched by the AGILE Board.
**Properties**: Shows adapter configuration, verification results, launchable status, and the default Worker Adapter. The Settings area is the source of truth; the AGILE Board displays the selected adapter status and links back to setup when launch is blocked.
**Relationships**: Produces launchable Worker Adapters. Supplies Launch Guardrail evidence for AGILE Board dispatch.

## Session
**Definition**: A single invocation of the Worker, bounded by start and end. The harness's primary unit of governance.
**Properties**: Has a token budget, a wall-clock duration, a set of tool invocations, and a zone state (green/yellow/red).
**Relationships**: Belongs to a Project. Consists of Tool Invocations. Evaluated by Checkpoints. Produces a Session Artifact.

## Task
**Definition**: A user-approved unit of coding work from the AGILE Board, with a description and an optional token estimate. Advisory, not enforced by the harness.
**Properties**: Has a description, acceptance criteria, an estimated token cost, and an actual token cost (populated after the session completes).
**Relationships**: May originate from manual entry, Markdown plan import, or long-task decomposition. Dispatched to a Session. Resides on the AGILE Board.

## Proposed Task Breakdown
**Definition**: A human-reviewed set of smaller candidate Tasks produced from a Markdown plan or oversized task before anything is added to the AGILE Board.
**Properties**: Uses tracer-bullet vertical slices: each proposed Task should be independently grabbable, narrow, demoable or verifiable on its own, and should cut through the needed product layers rather than splitting work by technical layer. Produced by a Task Breakdown Agent that reads all manual task input and Markdown imports, decides whether the work is a single Task or should be separated into multiple Tasks, and explains the decision. Shows candidate task titles, implementation prompts, acceptance criteria, dependencies, whether the slice is human-in-the-loop or autonomous, and decomposition confidence. It does not produce official token estimates or model recommendations.
**Relationships**: Produced during task intake when the Task Breakdown Agent decides the input is multi-task work. Reviewed and edited by the User. Accepted items are sent to Task Estimation; rejected items do not enter the AGILE Board.

## Task Breakdown Agent
**Definition**: The harness-owned orchestration agent that reads incoming manual task text or Markdown plans and decides whether the work should remain one Task or become a Proposed Task Breakdown.
**Properties**: Uses the Harness direct-provider transport path so its spend is tracked as Orchestration Tokens labeled task breakdown. It performs semantic decomposition rather than relying on simple length thresholds. It uses lightweight project context such as language, framework, test command, top-level folders, and project docs rather than inspecting arbitrary source files. It follows tracer-bullet vertical-slice rules and returns either a single-task decision or proposed smaller Tasks for human review.
**Relationships**: Runs before Task Estimation. Produces Proposed Task Breakdown for multi-task work. Sends single-task decisions directly to Task Estimation.

## Task Estimation
**Definition**: The LLM-assisted orchestration step where the Harness evaluates a Task before launch and produces a token estimate, complexity classification, model recommendation, confidence, rationale, assumptions, and risk flags.
**Properties**: Uses a harness-owned Estimator LLM distinct from the Worker model and Worker Adapter. Uses the Harness direct-provider transport path so estimator spend is tracked as Orchestration Tokens rather than hidden helper spend. Uses an accepted Task, lightweight project context, current budget context, and model-routing policy rather than a full repository scan. Produces structured output shown to the User before the Task becomes Estimated. The User can override the estimate or model before launch. If confidence is low, the User may run a Spike before accepting the estimate. If the Estimator LLM is unavailable or returns invalid output, the User may enter a manual estimate and model, clearly marked as manual rather than LLM-estimated. The Harness must not silently replace a failed Estimator LLM call with a heuristic product estimate. Manual estimates are launchable when required fields are present and Launch Guardrails pass. Estimator LLM tokens count against the daily budget as orchestration tokens, separate from Worker Session tokens.
**Relationships**: Runs after manual task entry or after the User accepts Proposed Task Breakdown items. Produces a Model Recommendation. May recommend a Spike. Successful estimation places a Task in Estimated; failed or invalid estimation places it in Blocked for manual estimate/model entry. Feeds Launch Guardrails and Session dispatch.

## Spike
**Definition**: A bounded pre-task Worker Session used to inspect enough project context to improve a low-confidence estimate before the real implementation begins.
**Properties**: Requires a launchable Worker Adapter because it is a Worker Session. By default it uses the same Worker Adapter and model intended for implementation, but the User may override to a cheaper or faster launchable adapter/model. It has no spike-specific token cap; normal daily and session guardrails still apply. It may inspect files, inspect configuration, and run targeted non-mutating tests or discovery commands, but must not modify production code, run destructive commands, broad test suites without approval, migrations, or commits. Its output is findings, revised estimate, risks, and launch recommendation.
**Relationships**: Triggered by low-confidence Task Estimation or by User choice. Counts against the daily budget as orchestration tokens labeled as spike, not Task actual implementation tokens. Automatically updates the Task estimate, recommended model, confidence, rationale, and risks, then returns the Task to Estimated with an updated-by-spike badge. The User still accepts the estimate and chooses the Worker before Ready/Launch.

## Orchestration Tokens
**Definition**: Tokens spent by the Harness itself to plan, estimate, validate, or coordinate work before or around Worker execution.
**Properties**: Count against the daily budget, but are labeled separately from Worker Session tokens so operator overhead does not distort task execution analytics.
**Relationships**: Produced by the Task Breakdown Agent, Task Estimation, Spikes, and Worker Adapter verification. Persisted token usage is labeled by usage kind: worker, task breakdown, estimation, spike, or adapter verification. Task Breakdown Agent tokens are labeled as task breakdown, not attached to Task implementation actuals, and shown as orchestration spend. Spike tokens are labeled as spike, not Task implementation actuals. Worker Adapter verification tokens are labeled as adapter verification, not attached to Task actuals, and hidden from the normal task board or marked as system verification. Shown separately from Worker tokens in Portal analytics while still counting toward the daily budget.

## Token Budget
**Definition**: A cap on token consumption, declared at two levels — daily (across all sessions) and per-session.
**Also known as**: Budget, Cap.
**Properties**: Expressed in tokens. Daily budget includes both Worker Session tokens and Orchestration Tokens. Per-session budget applies to Worker Session tokens. Budget state gates new launches before they start, but does not automatically halt a Worker Session mid-task. When an estimate exceeds remaining budget before launch, the User may explicitly approve a budget override; the Session is tagged as a budget override and audited. When exceeded during a running Session, the Harness records the overrun and raises alarms; user/admin manual abort remains available.
**Relationships**: Governed by Guardrails G1 and G2. Monitored by Checkpoint C1.

## Guardrail
**Definition**: A declared constraint that the harness enforces on the Worker. Every guardrail is explicit configuration, not implicit behavior.
**Properties**: Has a name, a threshold, and an enforcement action (context injection, alarm, or both). Never hard-stops the agent.
**Relationships**: Declared in the Guardrail Configuration. Enforced by the Proxy Engine. May trigger an Alarm.

## Launch Guardrail
**Definition**: A pre-run rule that prevents a Task from becoming Ready or Running unless the Harness can govern and observe the chosen Worker.
**Properties**: Validates that a Worker Adapter is configured, the working directory is valid, the selected model is allowed, session key wiring exists, and token tracking has been proven by launching the configured Worker Adapter through the Proxy Engine.
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
**Properties**: Columns represent orchestration state: Estimated (token/model recommendation produced), Ready (User accepted estimate/model and selected a launchable Worker Adapter), Running (Worker Session active), Review (Session ended and awaits human review), Done (accepted), and Blocked (estimation failed or task needs human change before launch or continuation). There is no full Scrum/Jira workflow and no normal unestimated Backlog because task intake exists to break down, estimate, and budget token spend. A task with a valid estimate but no verified Worker Adapter remains Estimated with Launch disabled rather than becoming Blocked. Each task card shows estimated vs. actual tokens, model recommendation, default Worker Adapter with per-task override, and linked Session results. Global budget state is visible while planning and dispatching work.
**Relationships**: Part of Material Handling. Contains Tasks. Produces estimates and Model Recommendations. Dispatches ready Tasks to a Worker through a Session. Returns Session Reports to the User. Accepts work through manual single-task entry, Markdown plan import with task breakdown, or long-task decomposition into multiple smaller Tasks. Current product docs, demo data, and tests should use the canonical board states; old Backlog language belongs only in clearly historical implementation plans.

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
